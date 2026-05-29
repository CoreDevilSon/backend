from typing import Any

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.category import Category


class CategoryError(ValueError):
    pass


def get_category(db: Session, category_id: int) -> Category | None:
    return db.get(Category, category_id)


def create_category(
    db: Session,
    *,
    name: str,
    parent_id: int | None,
    main_picture_url: str | None,
) -> Category:
    _validate_parent_exists(db, parent_id)
    _validate_parent_can_accept_children(db, parent_id)
    _validate_root_picture_rule(parent_id, main_picture_url)

    category = Category(
        name=name,
        parent_id=parent_id,
        main_picture_url=main_picture_url,
    )
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryError(_integrity_error_to_message(exc)) from exc

    db.refresh(category)
    return category


def update_category(db: Session, category: Category, updates: dict[str, Any]) -> Category:
    new_parent_id = updates["parent_id"] if "parent_id" in updates else category.parent_id
    new_picture = (
        updates["main_picture_url"] if "main_picture_url" in updates else category.main_picture_url
    )

    _validate_parent_exists(db, new_parent_id)
    if new_parent_id != category.parent_id:
        _validate_parent_can_accept_children(db, new_parent_id)
    _validate_not_self_parent(category.id, new_parent_id)
    _validate_no_cycle(db, category.id, new_parent_id)
    _validate_root_picture_rule(new_parent_id, new_picture)

    for key, value in updates.items():
        setattr(category, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryError(_integrity_error_to_message(exc)) from exc

    db.refresh(category)
    return category


def delete_category(db: Session, category: Category, mode: str) -> None:
    if mode == "reject":
        has_children = db.scalar(select(Category.id).where(Category.parent_id == category.id).limit(1))
        if has_children:
            raise CategoryError("Category has children; use mode=cascade or mode=reparent")

        db.delete(category)
        db.commit()
        return

    if mode == "reparent":
        has_children = db.scalar(select(Category.id).where(Category.parent_id == category.id).limit(1))
        if has_children:
            _validate_parent_can_accept_children(db, category.parent_id)

        db.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :new_parent_id,
                    updated_at = datetime('now')
                WHERE parent_id = :category_id
                """
            ),
            {"new_parent_id": category.parent_id, "category_id": category.id},
        )
        db.delete(category)
        db.commit()
        return

    if mode == "cascade":
        db.execute(
            text(
                """
                WITH RECURSIVE to_delete AS (
                    SELECT id
                    FROM categories
                    WHERE id = :category_id

                    UNION ALL

                    SELECT c.id
                    FROM categories c
                    JOIN to_delete d ON c.parent_id = d.id
                )
                DELETE FROM categories
                WHERE id IN (SELECT id FROM to_delete)
                """
            ),
            {"category_id": category.id},
        )
        db.commit()
        return

    raise CategoryError("Invalid delete mode")


def list_category_tree(db: Session, root_id: int | None = None) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            WITH RECURSIVE tree AS (
                SELECT
                    id,
                    parent_id,
                    name,
                    main_picture_url,
                    0 AS depth,
                    printf('%09d', id) AS path
                FROM categories
                WHERE (:root_id IS NULL AND parent_id IS NULL)
                   OR id = :root_id

                UNION ALL

                SELECT
                    c.id,
                    c.parent_id,
                    c.name,
                    c.main_picture_url,
                    tree.depth + 1 AS depth,
                    tree.path || '/' || printf('%09d', c.id) AS path
                FROM categories c
                JOIN tree ON c.parent_id = tree.id
            )
            SELECT id, parent_id, name, main_picture_url, path
            FROM tree
            ORDER BY path
            """
        ),
        {"root_id": root_id},
    ).mappings().all()

    nodes_by_id: dict[int, dict[str, Any]] = {}
    roots: list[dict[str, Any]] = []

    for row in rows:
        nodes_by_id[row["id"]] = {
            "id": row["id"],
            "name": row["name"],
            "parent_id": row["parent_id"],
            "main_picture_url": row["main_picture_url"],
            "children": [],
        }

    for row in rows:
        node = nodes_by_id[row["id"]]
        parent_id = row["parent_id"]

        if parent_id is not None and parent_id in nodes_by_id:
            nodes_by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


def list_category_properties(db: Session, category_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            WITH RECURSIVE ancestors AS (
                SELECT id, parent_id, 0 AS depth
                FROM categories
                WHERE id = :category_id

                UNION ALL

                SELECT c.id, c.parent_id, a.depth + 1
                FROM categories c
                JOIN ancestors a ON a.parent_id = c.id
            ),
            ranked_properties AS (
                SELECT
                    p.id,
                    p.name,
                    p.description,
                    p.type,
                    cp.category_id AS source_category_id,
                    c.name AS source_category_name,
                    CASE WHEN cp.category_id = :category_id THEN 1 ELSE 0 END AS is_direct,
                    a.depth,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.id
                        ORDER BY a.depth ASC
                    ) AS rn
                FROM ancestors a
                JOIN category_properties cp ON cp.category_id = a.id
                JOIN properties p ON p.id = cp.property_id
                JOIN categories c ON c.id = cp.category_id
            )
            SELECT
                rp.id,
                rp.name,
                rp.description,
                rp.type,
                rp.source_category_id,
                rp.source_category_name,
                rp.is_direct,
                cpv.value
            FROM ranked_properties rp
            LEFT JOIN category_property_values cpv
                ON cpv.category_id = rp.source_category_id AND cpv.property_id = rp.id
            WHERE rp.rn = 1
            ORDER BY rp.name ASC
            """
        ),
        {"category_id": category_id},
    ).mappings().all()

    return [dict(row) for row in rows]


def attach_property_to_category(
    db: Session,
    category_id: int,
    property_id: int,
    value: str | None = None,
) -> None:
    try:
        db.execute(
            text(
                """
                INSERT INTO category_properties (category_id, property_id)
                VALUES (:category_id, :property_id)
                """
            ),
            {"category_id": category_id, "property_id": property_id},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryError(_category_property_integrity_error_to_message(exc)) from exc

    if value is not None:
        set_category_property_value(db, category_id, property_id, value)


def set_category_property_value(
    db: Session,
    category_id: int,
    property_id: int,
    value: str | None,
) -> None:
    """Upsert the value for a (category, property) pair."""
    db.execute(
        text(
            """
            INSERT INTO category_property_values (category_id, property_id, value)
            VALUES (:category_id, :property_id, :value)
            ON CONFLICT(category_id, property_id)
            DO UPDATE SET value = excluded.value, updated_at = datetime('now')
            """
        ),
        {"category_id": category_id, "property_id": property_id, "value": value},
    )
    db.commit()


def detach_property_from_category(db: Session, category_id: int, property_id: int) -> None:
    exists = db.scalar(
        text(
            """
            SELECT 1
            FROM category_properties
            WHERE category_id = :category_id AND property_id = :property_id
            LIMIT 1
            """
        ),
        {"category_id": category_id, "property_id": property_id},
    )
    if not exists:
        raise CategoryError("Property is not directly attached to this category")

    db.execute(
        text(
            """
            DELETE FROM category_properties
            WHERE category_id = :category_id AND property_id = :property_id
            """
        ),
        {"category_id": category_id, "property_id": property_id},
    )
    db.commit()


def list_category_products(db: Session, category_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            WITH RECURSIVE descendants AS (
                SELECT id, 0 AS depth
                FROM categories
                WHERE id = :category_id

                UNION ALL

                SELECT c.id, d.depth + 1
                FROM categories c
                JOIN descendants d ON c.parent_id = d.id
            )
            SELECT
                p.id,
                p.name,
                p.description,
                cp.category_id AS source_category_id,
                c.name AS source_category_name,
                CASE WHEN cp.category_id = :category_id THEN 1 ELSE 0 END AS is_direct,
                d.depth
            FROM descendants d
            JOIN category_products cp ON cp.category_id = d.id
            JOIN products p ON p.id = cp.product_id
            JOIN categories c ON c.id = cp.category_id
            ORDER BY d.depth ASC, p.name ASC
            """
        ),
        {"category_id": category_id},
    ).mappings().all()

    photos_map: dict[int, list[str]] = {}
    for row in rows:
        photo_rows = db.execute(
            text(
                """
                SELECT photo_url
                FROM product_photos
                WHERE product_id = :product_id
                ORDER BY position ASC
                """
            ),
            {"product_id": row["id"]},
        ).mappings().all()
        photos_map[row["id"]] = [photo_row["photo_url"] for photo_row in photo_rows]

    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["photos"] = photos_map.get(row["id"], [])
        item["is_direct"] = bool(item.get("is_direct"))
        item.pop("depth", None)
        output.append(item)

    return output


def list_category_product_catalog(db: Session, category_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                p.id,
                p.name,
                p.description,
                cp.category_id AS attached_category_id,
                c.name AS attached_category_name
            FROM products p
            LEFT JOIN category_products cp ON cp.product_id = p.id
            LEFT JOIN categories c ON c.id = cp.category_id
            ORDER BY p.name ASC
            """
        )
    ).mappings().all()

    output: list[dict[str, Any]] = []
    for row in rows:
        photo_rows = db.execute(
            text(
                """
                SELECT photo_url
                FROM product_photos
                WHERE product_id = :product_id
                ORDER BY position ASC
                """
            ),
            {"product_id": row["id"]},
        ).mappings().all()

        attached_category_id = row["attached_category_id"]
        output.append(
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "photos": [photo_row["photo_url"] for photo_row in photo_rows],
                "attached_category_id": attached_category_id,
                "attached_category_name": row["attached_category_name"],
                "is_available_for_category": attached_category_id is None or attached_category_id == category_id,
            }
        )

    return output


def attach_product_to_category(db: Session, category_id: int, product_id: int) -> None:
    _validate_category_is_leaf(db, category_id)

    existing = db.execute(
        text(
            """
            SELECT cp.category_id, c.name AS category_name
            FROM category_products cp
            JOIN categories c ON c.id = cp.category_id
            WHERE cp.product_id = :product_id
            LIMIT 1
            """
        ),
        {"product_id": product_id},
    ).mappings().first()

    if existing:
        if existing["category_id"] == category_id:
            raise CategoryError("Product is already attached to this category")
        raise CategoryError(
            f"Product is already attached to category '{existing['category_name']}' and is unavailable"
        )

    try:
        db.execute(
            text(
                """
                INSERT INTO category_products (category_id, product_id)
                VALUES (:category_id, :product_id)
                """
            ),
            {"category_id": category_id, "product_id": product_id},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryError(_category_product_integrity_error_to_message(exc)) from exc


def detach_product_from_category(db: Session, category_id: int, product_id: int) -> None:
    exists = db.scalar(
        text(
            """
            SELECT 1
            FROM category_products
            WHERE category_id = :category_id AND product_id = :product_id
            LIMIT 1
            """
        ),
        {"category_id": category_id, "product_id": product_id},
    )
    if not exists:
        raise CategoryError("Product is not attached to this category")

    db.execute(
        text(
            """
            DELETE FROM category_products
            WHERE category_id = :category_id AND product_id = :product_id
            """
        ),
        {"category_id": category_id, "product_id": product_id},
    )
    db.commit()

def _validate_parent_exists(db: Session, parent_id: int | None) -> None:
    if parent_id is None:
        return

    parent = db.get(Category, parent_id)
    if parent is None:
        raise CategoryError("Parent category not found")


def _validate_parent_can_accept_children(db: Session, parent_id: int | None) -> None:
    if parent_id is None:
        return

    has_products = db.scalar(
        text(
            """
            SELECT 1
            FROM category_products
            WHERE category_id = :parent_id
            LIMIT 1
            """
        ),
        {"parent_id": parent_id},
    )
    if has_products:
        raise CategoryError("Cannot add subcategory under a category that has attached products")


def _validate_category_is_leaf(db: Session, category_id: int) -> None:
    has_children = db.scalar(
        text(
            """
            SELECT 1
            FROM categories
            WHERE parent_id = :category_id
            LIMIT 1
            """
        ),
        {"category_id": category_id},
    )
    if has_children:
        raise CategoryError("Products can only be attached to leaf categories")


def _validate_not_self_parent(category_id: int, parent_id: int | None) -> None:
    if parent_id is None:
        return

    if parent_id == category_id:
        raise CategoryError("Category cannot be its own parent")


def _validate_no_cycle(db: Session, category_id: int, new_parent_id: int | None) -> None:
    if new_parent_id is None:
        return

    is_descendant = db.scalar(
        text(
            """
            WITH RECURSIVE descendants AS (
                SELECT id
                FROM categories
                WHERE id = :category_id

                UNION ALL

                SELECT c.id
                FROM categories c
                JOIN descendants d ON c.parent_id = d.id
            )
            SELECT 1
            FROM descendants
            WHERE id = :new_parent_id
            LIMIT 1
            """
        ),
        {"category_id": category_id, "new_parent_id": new_parent_id},
    )

    if is_descendant:
        raise CategoryError("Cannot move category under its own descendant")


def _validate_root_picture_rule(parent_id: int | None, main_picture_url: str | None) -> None:
    if parent_id is not None and main_picture_url is not None:
        raise CategoryError(
            "main_picture_url is allowed only for root categories (parent_id must be null)"
        )


def _integrity_error_to_message(exc: IntegrityError) -> str:
    message = str(exc.orig)
    if "uq_categories_parent_name" in message or "UNIQUE constraint failed" in message:
        return "A sibling category with the same name already exists"
    if "ck_categories_root_picture_only" in message or "CHECK constraint failed" in message:
        return "main_picture_url is allowed only for root categories (parent_id must be null)"
    return "Category operation failed due to database constraint"


def _category_property_integrity_error_to_message(exc: IntegrityError) -> str:
    message = str(exc.orig)
    if "uq_category_properties_category_property" in message or "UNIQUE constraint failed" in message:
        return "Property is already attached to this category"
    if "FOREIGN KEY constraint failed" in message:
        return "Category or property does not exist"
    return "Category-property operation failed due to database constraint"


def _category_product_integrity_error_to_message(exc: IntegrityError) -> str:
    text_error = str(exc).lower()

    if "unique" in text_error:
        return "Product is already attached to this category"
    if "foreign key" in text_error:
        return "Invalid category or product reference"

    return "Failed to attach product to category"
