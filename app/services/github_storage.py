import base64
import json
import os
import re
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from backend.app.core.config import settings

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}


class GitHubStorageError(ValueError):
    pass


def upload_image_to_github(file_bytes: bytes, original_filename: str, folder: str | None = None) -> dict:
    owner, repo, branch, token = _validate_settings()
    _validate_repo_and_branch_access(owner=owner, repo=repo, branch=branch, token=token)

    safe_name, ext = _safe_filename(original_filename)
    _validate_extension(ext)

    storage_folder = _normalized_folder(folder or settings.github_image_base_path)
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}-{safe_name}{ext}"
    file_path = f"{storage_folder}/{filename}" if storage_folder else filename

    content_b64 = base64.b64encode(file_bytes).decode("ascii")

    payload = {
        "message": f"upload image: {file_path}",
        "content": content_b64,
        "branch": branch,
    }

    api_path = quote(file_path)
    api_url = (
        f"https://api.github.com/repos/{owner}/{repo}/contents/{api_path}"
    )

    response_data = _github_request("PUT", api_url, payload, token=token)

    content = response_data.get("content", {})
    commit = response_data.get("commit", {})

    raw_url = (
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
    )
    cdn_url = f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/{file_path}"

    return {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "file_path": file_path,
        "file_name": filename,
        "commit_sha": commit.get("sha", ""),
        "blob_url": content.get("html_url", ""),
        "download_url": content.get("download_url"),
        "raw_url": raw_url,
        "cdn_url": cdn_url,
    }


def _validate_settings() -> tuple[str, str, str, str]:
    token = settings.github_token.strip()
    owner = settings.github_repo_owner.strip()
    repo = settings.github_repo_name.strip()
    branch = settings.github_repo_branch.strip() or "main"

    missing = []
    if not token:
        missing.append("GITHUB_TOKEN")
    if not owner:
        missing.append("GITHUB_REPO_OWNER")
    if not repo:
        missing.append("GITHUB_REPO_NAME")

    if missing:
        raise GitHubStorageError(f"Missing required GitHub settings: {', '.join(missing)}")

    return owner, repo, branch, token


def _validate_repo_and_branch_access(*, owner: str, repo: str, branch: str, token: str) -> None:
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    branch_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{quote(branch)}"

    try:
        _github_request("GET", repo_url, payload=None, token=token)
    except GitHubStorageError as exc:
        raise GitHubStorageError(
            f"Repository lookup failed for {owner}/{repo}. "
            "Verify owner/repo are correct and token can access this repository. "
            f"Original error: {exc}"
        ) from exc

    try:
        _github_request("GET", branch_url, payload=None, token=token)
    except GitHubStorageError as exc:
        raise GitHubStorageError(
            f"Branch lookup failed for {owner}/{repo} branch '{branch}'. "
            "Verify branch name and that it exists. "
            f"Original error: {exc}"
        ) from exc


def _safe_filename(filename: str) -> tuple[str, str]:
    base = os.path.basename(filename)
    stem, ext = os.path.splitext(base)

    if not stem:
        stem = "image"

    safe_stem = re.sub(r"[^a-zA-Z0-9_-]", "-", stem).strip("-")
    if not safe_stem:
        safe_stem = "image"

    return safe_stem.lower(), ext.lower()


def _validate_extension(ext: str) -> None:
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise GitHubStorageError(
            "Unsupported image file type. Allowed: jpg, jpeg, png, gif, webp, bmp, svg"
        )


def _normalized_folder(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().strip("/")


def _github_request(method: str, url: str, payload: dict | None, token: str) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(
        url=url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "mmd-backend-uploader",
        },
    )

    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return _parse_json(raw)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else ""
        raise GitHubStorageError(
            f"GitHub API request failed ({exc.code}). {detail or 'No additional details.'}"
        ) from exc
    except URLError as exc:
        raise GitHubStorageError(f"Network error while reaching GitHub: {exc.reason}") from exc


def _parse_json(text: str) -> dict:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise GitHubStorageError("Unexpected response from GitHub API")
    return data
