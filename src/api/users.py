"""REST API endpoints for user management."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.schemas import UserCreate, UserUpdate, UserProfile, PhotoResponse
from src.services import user_service, photo_service
from src.utils.security import verify_jwt_token, create_jwt_token

logger = logging.getLogger("suhird.api.users")

router = APIRouter(prefix="/api/users", tags=["users"])


def _verify_auth(authorization: str = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.replace("Bearer ", "")
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@router.post("", response_model=UserProfile)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user (admin/testing endpoint)."""
    existing = await user_service.get_user_by_phone(db, body.phone)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    user = await user_service.create_user(db, body.phone)
    return UserProfile(
        id=user.id,
        created_at=user.created_at,
    )


@router.post("/auth")
async def authenticate(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Get JWT token for a phone number (creates user if needed)."""
    user = await user_service.get_user_by_phone(db, body.phone)
    if not user:
        user = await user_service.create_user(db, body.phone)
    token = create_jwt_token({"sub": str(user.id), "phone": body.phone})
    return {"access_token": token, "token_type": "bearer", "user_id": str(user.id)}


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(user_id: UUID, auth: dict = Depends(_verify_auth), db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    photos = await photo_service.get_photos(db, user_id)
    return UserProfile(
        id=user.id,
        name=user.name,
        age=user.age,
        gender=user.gender,
        location=user.location,
        bio_prompts=user.bio_prompts or {},
        preferences=user.preferences or {},
        lifestyle=user.lifestyle or {},
        values_data=user.values_data or {},
        interests=user.interests or [],
        relationship_type=user.relationship_type,
        onboarding_complete=user.onboarding_complete,
        photo_count=len(photos),
        created_at=user.created_at,
    )


@router.put("/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    auth: dict = Depends(_verify_auth),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.update_profile(db, user_id, body.model_dump(exclude_none=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    photos = await photo_service.get_photos(db, user_id)
    return UserProfile(
        id=user.id,
        name=user.name,
        age=user.age,
        gender=user.gender,
        location=user.location,
        bio_prompts=user.bio_prompts or {},
        preferences=user.preferences or {},
        lifestyle=user.lifestyle or {},
        values_data=user.values_data or {},
        interests=user.interests or [],
        relationship_type=user.relationship_type,
        onboarding_complete=user.onboarding_complete,
        photo_count=len(photos),
        created_at=user.created_at,
    )


@router.post("/{user_id}/photos")
async def upload_photo(
    user_id: UUID,
    file: UploadFile = File(...),
    position: int = 1,
    auth: dict = Depends(_verify_auth),
    db: AsyncSession = Depends(get_db),
):
    if position < 1 or position > 6:
        raise HTTPException(status_code=400, detail="Position must be 1-6")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    photo = await photo_service.upload_photo(db, user_id, content, position)
    return {
        "id": str(photo.id),
        "user_id": str(user_id),
        "position": photo.position,
        "url": photo_service.get_photo_url(user_id, position),
    }


@router.get("/{user_id}/photos/{position}")
async def get_photo(user_id: UUID, position: int):
    """Redirect to the static photo file."""
    from fastapi.responses import RedirectResponse
    url = photo_service.get_photo_url(user_id, position)
    return RedirectResponse(url=url)
