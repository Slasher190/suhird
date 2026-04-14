from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    phone: str


class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    location: str | None = None
    bio_prompts: dict | None = None
    preferences: dict | None = None
    lifestyle: dict | None = None
    values_data: dict | None = None
    interests: list[str] | None = None
    relationship_type: str | None = None


class UserProfile(BaseModel):
    id: UUID
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    location: str | None = None
    bio_prompts: dict = {}
    preferences: dict = {}
    lifestyle: dict = {}
    values_data: dict = {}
    interests: list[str] = []
    relationship_type: str | None = None
    onboarding_complete: bool = False
    photo_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoResponse(BaseModel):
    id: UUID
    user_id: UUID
    position: int
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchProfile(BaseModel):
    """Profile card shown to users during matching."""
    id: UUID
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    location: str | None = None
    bio_prompts: dict = {}
    interests: list[str] = []
    lifestyle: dict = {}
    relationship_type: str | None = None
    photo_urls: list[str] = []
    score: float = 0.0

    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    matches: list[MatchProfile]
    has_more: bool = False
    batch_number: int = 1


class InteractionCreate(BaseModel):
    target_user_id: UUID
    action: str = Field(..., pattern="^(like|pass)$")


class MutualMatchNotification(BaseModel):
    match_id: UUID
    user_a: MatchProfile
    user_b: MatchProfile
    matched_at: datetime


class BlockCreate(BaseModel):
    blocked_id: UUID
    reason: str | None = None


class OpenResponsesRequest(BaseModel):
    """Incoming request from OpenClaw via OpenResponses API."""
    model: str | None = None
    input: str | list | None = None
    stream: bool = False
    metadata: dict | None = None

    # OpenClaw may wrap the payload in a body key
    body: dict | None = None


class OpenResponsesMessage(BaseModel):
    type: str = "message"
    role: str = "assistant"
    content: list[dict]


class OpenResponsesResult(BaseModel):
    id: str
    object: str = "response"
    status: str = "completed"
    output: list[dict]
    usage: dict = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
