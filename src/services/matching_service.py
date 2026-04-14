"""
Matching engine for Suhird.

Three-component scoring:
  30% Structured (age, location, stated preferences)
  30% Semantic   (Qdrant vector similarity on bio/interests)
  40% MemPalace  (learned from like/skip behavior)
"""
import logging
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import User, Interaction, Match, Block
from src.services import user_service, photo_service, mempalace_service
from src.services.qdrant_service import search_similar
from src.bot import messages as msg

logger = logging.getLogger("suhird.matching")

WEIGHT_STRUCTURED = 0.30
WEIGHT_SEMANTIC = 0.30
WEIGHT_MEMPALACE = 0.40


async def get_matches(
    db: AsyncSession,
    user_id: UUID,
    batch_size: int = 5,
    exclude_ids: list[str] | None = None,
) -> list[dict]:
    """
    Return top-N match candidates for a user, combining all three scoring components.
    """
    user = await user_service.get_user(db, user_id)
    if not user or not user.onboarding_complete:
        return []

    # Gather IDs to exclude: already interacted + blocked + explicitly excluded
    interacted_ids = await _get_interacted_ids(db, user_id)
    blocked_ids = await _get_blocked_ids(db, user_id)
    all_exclude = interacted_ids | blocked_ids
    if exclude_ids:
        all_exclude.update(exclude_ids)

    # Get all eligible candidates from DB
    candidates = await user_service.get_all_complete_users(db, exclude_id=user_id)
    candidates = [c for c in candidates if str(c.id) not in all_exclude]

    if not candidates:
        return []

    user_data = _user_to_dict(user)

    # -- Semantic scores from Qdrant --
    semantic_scores = {}
    try:
        qdrant_results = await search_similar(
            user_id, user_data, limit=50, exclude_ids=list(all_exclude)
        )
        for r in qdrant_results:
            semantic_scores[r["user_id"]] = r["score"]
    except Exception as e:
        logger.warning("Qdrant search failed (using 0.5 fallback): %s", e)

    # -- Score each candidate --
    scored = []
    for candidate in candidates:
        cid = str(candidate.id)
        c_data = _user_to_dict(candidate)

        structured = _structured_score(user_data, c_data)
        semantic = semantic_scores.get(cid, 0.5)

        try:
            mempalace = await mempalace_service.score_candidate(user_id, c_data)
        except Exception:
            mempalace = 0.5

        final = (
            WEIGHT_STRUCTURED * structured
            + WEIGHT_SEMANTIC * semantic
            + WEIGHT_MEMPALACE * mempalace
        )

        photos = await photo_service.get_photos(db, candidate.id)
        photo_urls = photo_service.get_all_photo_urls(candidate.id, photos)

        scored.append({
            "id": cid,
            "name": candidate.name,
            "age": candidate.age,
            "gender": candidate.gender,
            "location": candidate.location,
            "bio_prompts": candidate.bio_prompts or {},
            "interests": candidate.interests or [],
            "lifestyle": candidate.lifestyle or {},
            "relationship_type": candidate.relationship_type,
            "photo_urls": photo_urls,
            "score": round(final, 4),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:batch_size]


def _structured_score(user: dict, candidate: dict) -> float:
    """Score based on explicit preferences and compatibility. Returns 0.0-1.0."""
    score = 0.0
    factors = 0

    # Gender preference match
    prefs = user.get("preferences", {})
    looking_for = prefs.get("looking_for_gender", "everyone")
    c_gender = candidate.get("gender", "")
    if looking_for == "everyone":
        score += 1.0
    elif looking_for == "men" and c_gender == "male":
        score += 1.0
    elif looking_for == "women" and c_gender == "female":
        score += 1.0
    factors += 1

    # Age range match
    age_range = prefs.get("age_range", {})
    c_age = candidate.get("age", 0)
    if age_range and c_age:
        min_age = age_range.get("min", 18)
        max_age = age_range.get("max", 100)
        if min_age <= c_age <= max_age:
            score += 1.0
        else:
            diff = min(abs(c_age - min_age), abs(c_age - max_age))
            score += max(0, 1.0 - diff * 0.1)
    else:
        score += 0.5
    factors += 1

    # Location match
    u_loc = (user.get("location") or "").lower()
    c_loc = (candidate.get("location") or "").lower()
    if u_loc and c_loc:
        if u_loc == c_loc:
            score += 1.0
        elif _same_state(u_loc, c_loc):
            score += 0.7
        else:
            score += 0.3
    else:
        score += 0.5
    factors += 1

    # Relationship type alignment
    u_rel = user.get("relationship_type", "")
    c_rel = candidate.get("relationship_type", "")
    if u_rel and c_rel:
        if u_rel == c_rel:
            score += 1.0
        elif {u_rel, c_rel} & {"not sure"}:
            score += 0.7
        else:
            score += 0.4
    else:
        score += 0.5
    factors += 1

    # Lifestyle compatibility
    u_life = user.get("lifestyle", {})
    c_life = candidate.get("lifestyle", {})
    if u_life and c_life:
        life_keys = ["smoking", "drinking", "diet", "exercise", "social_style"]
        life_matches = sum(1 for k in life_keys if u_life.get(k) == c_life.get(k))
        score += life_matches / max(len(life_keys), 1)
    else:
        score += 0.5
    factors += 1

    # Interest overlap
    u_interests = set(user.get("interests", []))
    c_interests = set(candidate.get("interests", []))
    if u_interests and c_interests:
        overlap = len(u_interests & c_interests)
        total = len(u_interests | c_interests)
        score += overlap / max(total, 1)
    else:
        score += 0.3
    factors += 1

    return score / max(factors, 1)


def _same_state(loc1: str, loc2: str) -> bool:
    """Rough check: if any word > 3 chars is shared, assume same state."""
    words1 = {w for w in loc1.split(",") if len(w.strip()) > 3}
    words2 = {w for w in loc2.split(",") if len(w.strip()) > 3}
    return bool(words1 & words2)


def _user_to_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "location": user.location,
        "bio_prompts": user.bio_prompts or {},
        "preferences": user.preferences or {},
        "lifestyle": user.lifestyle or {},
        "values_data": user.values_data or {},
        "interests": user.interests or [],
        "relationship_type": user.relationship_type,
    }


async def record_interaction(
    db: AsyncSession, user_id: UUID, target_id: UUID, action: str
) -> None:
    """Record a like or pass interaction."""
    interaction = Interaction(user_id=user_id, target_user_id=target_id, action=action)
    db.add(interaction)
    await db.flush()

    # Store in MemPalace for preference learning
    target = await user_service.get_user(db, target_id)
    if target:
        target_data = _user_to_dict(target)
        try:
            await mempalace_service.store_interaction(user_id, target_id, action, target_data)
        except Exception as e:
            logger.warning("MemPalace store failed (non-fatal): %s", e)


async def check_mutual_match(db: AsyncSession, user_id: UUID, target_id: UUID) -> str | None:
    """Check if target has also liked user. If so, create match and return notification."""
    result = await db.execute(
        select(Interaction).where(
            and_(
                Interaction.user_id == target_id,
                Interaction.target_user_id == user_id,
                Interaction.action == "like",
            )
        )
    )
    reciprocal = result.scalar_one_or_none()

    if not reciprocal:
        return None

    # Check if match already exists
    existing = await db.execute(
        select(Match).where(
            ((Match.user_a_id == user_id) & (Match.user_b_id == target_id))
            | ((Match.user_a_id == target_id) & (Match.user_b_id == user_id))
        )
    )
    if existing.scalar_one_or_none():
        return None

    # Create match
    match = Match(user_a_id=user_id, user_b_id=target_id)
    db.add(match)
    await db.flush()

    target_user = await user_service.get_user(db, target_id)
    target_phone = await user_service.get_user_phone(db, target_id)

    notification = msg.MUTUAL_MATCH.format(
        match_name=target_user.name or "Your match",
        match_phone=target_phone or "Contact will be shared",
    )

    # Send notification to the other user via OpenClaw gateway
    try:
        await _notify_mutual_match(db, user_id, target_id)
    except Exception as e:
        logger.warning("Failed to notify other user (non-fatal): %s", e)

    logger.info("Mutual match created: %s <-> %s", user_id, target_id)
    return notification


async def _notify_mutual_match(db: AsyncSession, user_id: UUID, target_id: UUID) -> None:
    """Send mutual match notification to the other user via OpenClaw gateway."""
    import httpx
    from src.config import settings

    user = await user_service.get_user(db, user_id)
    user_phone = await user_service.get_user_phone(db, user_id)
    target_phone = await user_service.get_user_phone(db, target_id)

    if not target_phone or not user_phone:
        return

    notification_text = msg.MUTUAL_MATCH_OTHER.format(
        match_name=user.name or "Someone",
        match_phone=user_phone,
    )

    # Send via OpenClaw gateway
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(
                f"{settings.openclaw_gateway_url}/v1/responses",
                headers={
                    "Authorization": f"Bearer {settings.openclaw_gateway_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "suhird-bot/matchmaker",
                    "input": notification_text,
                    "metadata": {
                        "deliver": True,
                        "channel": "whatsapp",
                        "to": target_phone,
                    },
                },
            )
        except Exception as e:
            logger.warning("OpenClaw notification failed: %s", e)


async def _get_interacted_ids(db: AsyncSession, user_id: UUID) -> set[str]:
    result = await db.execute(
        select(Interaction.target_user_id).where(Interaction.user_id == user_id)
    )
    return {str(row[0]) for row in result.fetchall()}


async def _get_blocked_ids(db: AsyncSession, user_id: UUID) -> set[str]:
    result = await db.execute(
        select(Block.blocked_id).where(Block.blocker_id == user_id)
    )
    return {str(row[0]) for row in result.fetchall()}


async def get_mutual_matches(db: AsyncSession, user_id: UUID) -> list[dict]:
    """Return all mutual matches for a user."""
    result = await db.execute(
        select(Match).where(
            (Match.user_a_id == user_id) | (Match.user_b_id == user_id)
        )
    )
    matches = result.scalars().all()

    mutual = []
    for m in matches:
        other_id = m.user_b_id if m.user_a_id == user_id else m.user_a_id
        other_user = await user_service.get_user(db, other_id)
        if other_user:
            photos = await photo_service.get_photos(db, other_id)
            mutual.append({
                "match_id": str(m.id),
                "matched_at": m.matched_at.isoformat() if m.matched_at else None,
                "user": {
                    "id": str(other_user.id),
                    "name": other_user.name,
                    "age": other_user.age,
                    "location": other_user.location,
                    "photo_urls": photo_service.get_all_photo_urls(other_id, photos),
                },
            })
    return mutual
