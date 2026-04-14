"""REST API endpoints for matching."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Block, Interaction
from src.schemas import InteractionCreate, BlockCreate
from src.services import matching_service, mempalace_service, user_service
from src.utils.security import verify_jwt_token

logger = logging.getLogger("suhird.api.matches")

router = APIRouter(prefix="/api", tags=["matches"])


def _verify_auth(authorization: str = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.replace("Bearer ", "")
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@router.get("/users/{user_id}/matches")
async def get_matches(
    user_id: UUID,
    batch_size: int = 5,
    auth: dict = Depends(_verify_auth),
    db: AsyncSession = Depends(get_db),
):
    matches = await matching_service.get_matches(db, user_id, batch_size=batch_size)
    return {"matches": matches, "count": len(matches)}


@router.post("/matches/{target_id}/like")
async def like_profile(
    target_id: UUID,
    auth: dict = Depends(_verify_auth),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(auth["sub"])

    target = await user_service.get_user(db, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")

    # Check for existing interaction
    existing = await db.execute(
        select(Interaction).where(
            and_(Interaction.user_id == user_id, Interaction.target_user_id == target_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already interacted with this user")

    await matching_service.record_interaction(db, user_id, target_id, "like")
    mutual_msg = await matching_service.check_mutual_match(db, user_id, target_id)

    return {
        "status": "liked",
        "mutual_match": mutual_msg is not None,
        "message": mutual_msg,
    }


@router.post("/matches/{target_id}/pass")
async def pass_profile(
    target_id: UUID,
    auth: dict = Depends(_verify_auth),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(auth["sub"])

    target = await user_service.get_user(db, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")

    existing = await db.execute(
        select(Interaction).where(
            and_(Interaction.user_id == user_id, Interaction.target_user_id == target_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already interacted with this user")

    await matching_service.record_interaction(db, user_id, target_id, "pass")
    return {"status": "passed"}


@router.get("/matches/mutual")
async def get_mutual_matches(
    auth: dict = Depends(_verify_auth),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(auth["sub"])
    matches = await matching_service.get_mutual_matches(db, user_id)
    return {"mutual_matches": matches, "count": len(matches)}


@router.post("/blocks")
async def block_user(
    body: BlockCreate,
    auth: dict = Depends(_verify_auth),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(auth["sub"])

    existing = await db.execute(
        select(Block).where(
            and_(Block.blocker_id == user_id, Block.blocked_id == body.blocked_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already blocked")

    block = Block(blocker_id=user_id, blocked_id=body.blocked_id, reason=body.reason)
    db.add(block)
    await db.flush()

    return {"status": "blocked", "blocked_id": str(body.blocked_id)}
