import logging
from uuid import UUID

import httpx

from src.config import settings

logger = logging.getLogger("suhird.mempalace")


async def store_interaction(
    user_id: UUID,
    target_user_id: UUID,
    action: str,
    target_profile: dict,
) -> None:
    """Store a like/skip interaction in MemPalace for preference learning."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.mempalace_url}/store",
                json={
                    "user_id": str(user_id),
                    "target_user_id": str(target_user_id),
                    "action": action,
                    "target_profile": target_profile,
                },
            )
            response.raise_for_status()
            logger.info("Stored %s interaction for user %s -> %s", action, user_id, target_user_id)
    except Exception as e:
        logger.warning("MemPalace store failed (non-fatal): %s", e)


async def query_preferences(user_id: UUID) -> dict:
    """Query learned preferences for a user from MemPalace."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.mempalace_url}/query",
                json={"user_id": str(user_id)},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning("MemPalace query failed (non-fatal): %s", e)
        return {}


async def score_candidate(user_id: UUID, candidate_profile: dict) -> float:
    """Score a candidate profile against a user's learned preferences. Returns 0.0-1.0."""
    preferences = await query_preferences(user_id)
    if not preferences:
        return 0.5  # neutral score when no preference data available

    score = 0.5
    liked_attrs = preferences.get("liked_attributes", {})
    skipped_attrs = preferences.get("skipped_attributes", {})

    for attr, weight in liked_attrs.items():
        if attr in str(candidate_profile):
            score += weight * 0.1

    for attr, weight in skipped_attrs.items():
        if attr in str(candidate_profile):
            score -= weight * 0.1

    return max(0.0, min(1.0, score))
