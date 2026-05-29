from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.app.schemas.upload import GitHubImageUploadResponse
from backend.app.services.github_storage import GitHubStorageError, upload_image_to_github

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


@router.post("/github-image", response_model=GitHubImageUploadResponse)
async def upload_github_image(
    image: UploadFile = File(...),
    folder: str | None = Form(default=None),
) -> GitHubImageUploadResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are allowed",
        )

    file_bytes = await image.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image too large. Maximum allowed size is 10MB",
        )

    try:
        result = upload_image_to_github(
            file_bytes=file_bytes,
            original_filename=image.filename or "image",
            folder=folder,
        )
    except GitHubStorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return GitHubImageUploadResponse(**result)
