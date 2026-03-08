from pydantic import BaseModel, HttpUrl


class ProfileCreate(BaseModel):
    full_name: str
    aliases: list[str] = []
    known_handles: list[str] = []
    description: str | None = None


class DiscoverRequest(BaseModel):
    platforms: list[str] = ["youtube", "x"]
    max_candidates_per_query: int = 10


class ManualCandidateCreate(BaseModel):
    platform: str
    external_id: str
    url: HttpUrl
    title: str | None = None
    description: str | None = None
    account_name: str | None = None
    posted_at_raw: str | None = None


class ReviewUpdate(BaseModel):
    review_status: str
    review_notes: str | None = None
