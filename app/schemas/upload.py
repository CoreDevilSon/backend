from pydantic import BaseModel


class GitHubImageUploadResponse(BaseModel):
    provider: str = "github"
    owner: str
    repo: str
    branch: str
    file_path: str
    file_name: str
    commit_sha: str
    blob_url: str
    download_url: str | None = None
    raw_url: str
    cdn_url: str
