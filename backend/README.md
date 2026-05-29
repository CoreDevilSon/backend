# MMD Backend

UV-based Python backend with FastAPI, SQLAlchemy, Alembic migrations, Pydantic settings, and an admin seed script.

## Setup

### 1) Install dependencies (from project root or backend folder)

```powershell
uv sync
```

### 2) Configure environment variables

From the `backend` folder:

```powershell
Copy-Item .env.example .env
```

Update values in `.env` (especially `ADMIN_PASSWORD`).

### 3) Run database migrations

Migrations can be run from the **project root**:

```powershell
uv run alembic upgrade head
uv run alembic current
```

Or from the `backend` folder:

```powershell
& .\.venv\Scripts\python.exe -m alembic upgrade head
```

### 4) Seed admin account (from backend folder)

```powershell
uv run python scripts/seed_admin.py
```

### 5) Start API server (from backend folder)

```powershell
uv run uvicorn app.main:app --reload
```

Health endpoint:

- GET `http://127.0.0.1:8000/health`

## Categories API

The categories feature supports infinite nesting via `parent_id` and enforces that `main_picture_url` is set only for root categories (`parent_id = null`).

- POST `/api/v1/categories`
- PATCH `/api/v1/categories/{category_id}`
- DELETE `/api/v1/categories/{category_id}?mode=reject|cascade|reparent`
- GET `/api/v1/categories/tree`

### Example create root category

```json
{
  "name": "Electronics",
  "parent_id": null,
  "main_picture_url": "https://cdn.example.com/cat/electronics.jpg"
}
```

### Example create subcategory

```json
{
  "name": "Laptops",
  "parent_id": 1,
  "main_picture_url": null
}
```

### Example tree response

```json
[
  {
    "id": 1,
    "name": "Electronics",
    "parent_id": null,
    "main_picture_url": "https://cdn.example.com/cat/electronics.jpg",
    "children": [
      {
        "id": 2,
        "name": "Laptops",
        "parent_id": 1,
        "main_picture_url": null,
        "children": []
      }
    ]
  }
]
```

## GitHub Image Upload API

Upload an image file to a GitHub repository and receive reusable public links.

- POST `/api/v1/uploads/github-image`
- Content type: `multipart/form-data`
- Form fields:
  - `image` (required): image file
  - `folder` (optional): override destination folder inside repo

### Required environment variables

- `GITHUB_TOKEN`: GitHub token with contents write access
- `GITHUB_REPO_OWNER`: repo owner/org name
- `GITHUB_REPO_NAME`: repository name
- `GITHUB_REPO_BRANCH`: target branch (default `main`)
- `GITHUB_IMAGE_BASE_PATH`: default upload folder (default `uploads/images`)

### Example cURL

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/uploads/github-image" \
  -F "image=@C:/images/photo.jpg" \
  -F "folder=categories"
```

### Example response

```json
{
  "provider": "github",
  "owner": "your-org",
  "repo": "your-repo",
  "branch": "main",
  "file_path": "categories/20260512090130-photo.jpg",
  "file_name": "20260512090130-photo.jpg",
  "commit_sha": "abc123...",
  "blob_url": "https://github.com/your-org/your-repo/blob/main/categories/20260512090130-photo.jpg",
  "download_url": "https://raw.githubusercontent.com/...",
  "raw_url": "https://raw.githubusercontent.com/your-org/your-repo/main/categories/20260512090130-photo.jpg",
  "cdn_url": "https://cdn.jsdelivr.net/gh/your-org/your-repo@main/categories/20260512090130-photo.jpg"
}
```

## Create new migrations

```powershell
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```
