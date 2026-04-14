"""
Central message handler for Suhird bot.

Receives a phone number + message text, manages conversation state via Redis,
and routes to the appropriate handler (onboarding, browsing, matching actions).
"""
import json
import logging
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot import messages as msg
from src.bot.onboarding import QUESTIONS, TOTAL_QUESTIONS, get_question, get_section_for_index, state_for_section
from src.bot.states import ConversationState
from src.services import user_service, photo_service

logger = logging.getLogger("suhird.handler")


class Session:
    """Wrapper around Redis session data for a phone number."""

    def __init__(self, phone: str, data: dict | None = None):
        self.phone = phone
        self.data = data or {
            "state": ConversationState.NEW.value,
            "question_index": 0,
            "user_id": None,
            "profile_data": {},
            "current_batch": [],
            "batch_number": 0,
            "shown_ids": [],
        }

    @property
    def state(self) -> str:
        return self.data.get("state", ConversationState.NEW.value)

    @state.setter
    def state(self, value: str):
        self.data["state"] = value

    @property
    def question_index(self) -> int:
        return self.data.get("question_index", 0)

    @question_index.setter
    def question_index(self, value: int):
        self.data["question_index"] = value

    @property
    def user_id(self) -> str | None:
        return self.data.get("user_id")

    @user_id.setter
    def user_id(self, value: str):
        self.data["user_id"] = value

    @property
    def profile_data(self) -> dict:
        return self.data.get("profile_data", {})

    @profile_data.setter
    def profile_data(self, value: dict):
        self.data["profile_data"] = value

    @property
    def current_batch(self) -> list:
        return self.data.get("current_batch", [])

    @current_batch.setter
    def current_batch(self, value: list):
        self.data["current_batch"] = value

    @property
    def batch_number(self) -> int:
        return self.data.get("batch_number", 0)

    @batch_number.setter
    def batch_number(self, value: int):
        self.data["batch_number"] = value

    @property
    def shown_ids(self) -> list:
        return self.data.get("shown_ids", [])

    def add_shown_ids(self, ids: list[str]):
        shown = set(self.shown_ids)
        shown.update(ids)
        self.data["shown_ids"] = list(shown)

    def to_json(self) -> str:
        return json.dumps(self.data)


async def load_session(redis_client: aioredis.Redis, phone: str) -> Session:
    key = f"session:{phone}"
    raw = await redis_client.get(key)
    if raw:
        return Session(phone, json.loads(raw))
    return Session(phone)


async def save_session(redis_client: aioredis.Redis, session: Session):
    key = f"session:{session.phone}"
    await redis_client.set(key, session.to_json(), ex=86400 * 7)  # 7-day TTL


async def handle_message(
    phone: str,
    text: str,
    redis_client: aioredis.Redis,
    db: AsyncSession,
    is_photo: bool = False,
    photo_bytes: bytes | None = None,
) -> str:
    """
    Process an incoming message and return a response string.

    Args:
        phone: sender's phone number (e.g. +918529126697)
        text: message body
        redis_client: Redis connection
        db: database session
        is_photo: whether the message is a photo upload
        photo_bytes: raw photo bytes if is_photo
    """
    session = await load_session(redis_client, phone)
    text_lower = text.strip().lower() if text else ""

    # Global commands available at any state
    if text_lower == "help":
        return msg.HELP_TEXT

    if text_lower == "my profile" and session.user_id:
        return await _show_profile(session, db)

    # Route by state
    state = session.state

    if state == ConversationState.NEW.value:
        response = await _handle_new_user(session, phone, db)

    elif state in {
        ConversationState.ONBOARDING_BASIC.value,
        ConversationState.ONBOARDING_BIO.value,
        ConversationState.ONBOARDING_PREFERENCES.value,
        ConversationState.ONBOARDING_LIFESTYLE.value,
        ConversationState.ONBOARDING_VALUES.value,
        ConversationState.ONBOARDING_INTERESTS.value,
    }:
        response = await _handle_onboarding(session, text, db)

    elif state == ConversationState.ONBOARDING_PHOTOS.value:
        response = await _handle_photo_upload(session, text, is_photo, photo_bytes, db)

    elif state == ConversationState.PROFILE_COMPLETE.value:
        response = await _handle_complete_profile(session, text_lower, db)

    elif state in {ConversationState.BROWSING.value, ConversationState.AWAITING_ACTION.value}:
        response = await _handle_browsing(session, text_lower, db)

    else:
        response = msg.HELP_TEXT

    await save_session(redis_client, session)
    return response


async def _handle_new_user(session: Session, phone: str, db: AsyncSession) -> str:
    existing = await user_service.get_user_by_phone(db, phone)

    if existing:
        session.user_id = str(existing.id)
        if existing.onboarding_complete:
            session.state = ConversationState.PROFILE_COMPLETE.value
            return msg.WELCOME_BACK + "\n\n" + msg.HELP_TEXT
        else:
            session.question_index = existing.onboarding_step or 0
            section = get_section_for_index(session.question_index)
            session.state = state_for_section(section).value
            q = get_question(session.question_index)
            return msg.WELCOME_BACK + "\n\n" + (q.text if q else msg.HELP_TEXT)
    else:
        user = await user_service.create_user(db, phone)
        session.user_id = str(user.id)
        session.question_index = 0
        section = get_section_for_index(0)
        session.state = state_for_section(section).value
        first_q = get_question(0)
        return msg.WELCOME + "\n\n" + first_q.text


async def _handle_onboarding(session: Session, text: str, db: AsyncSession) -> str:
    q = get_question(session.question_index)
    if not q:
        return await _finish_onboarding(session, db)

    valid, value = q.validate(text)
    if not valid:
        return msg.INVALID_INPUT.format(hint=q.error_hint) + "\n\n" + q.text

    # Store the answer in profile_data
    pd = session.profile_data
    if q.store_key:
        if q.store_field not in pd:
            pd[q.store_field] = {}
        pd[q.store_field][q.store_key] = value
    else:
        pd[q.store_field] = value
    session.profile_data = pd

    # Persist to DB periodically (every section boundary or every 4 questions)
    session.question_index += 1

    if session.question_index % 4 == 0 or session.question_index >= TOTAL_QUESTIONS:
        await _persist_profile(session, db)

    if session.question_index >= TOTAL_QUESTIONS:
        # Move to photo upload
        session.state = ConversationState.ONBOARDING_PHOTOS.value
        return "Great answers! 🎉\n\n" + msg.PHOTO_REQUEST

    # Advance to next question
    next_q = get_question(session.question_index)
    section = get_section_for_index(session.question_index)
    session.state = state_for_section(section).value
    return next_q.text


async def _handle_photo_upload(
    session: Session, text: str, is_photo: bool, photo_bytes: bytes | None, db: AsyncSession
) -> str:
    text_lower = (text or "").strip().lower()

    if text_lower in {"skip", "done"}:
        return await _finish_onboarding(session, db)

    if is_photo and photo_bytes:
        user_id = UUID(session.user_id)
        photos = await photo_service.get_photos(db, user_id)
        position = len(photos) + 1

        if position > 6:
            return msg.PHOTO_LIMIT

        await photo_service.upload_photo(db, user_id, photo_bytes, position)

        if position >= 6:
            return msg.PHOTO_LIMIT + "\n\n" + "Type *done* to finish."

        return msg.PHOTO_RECEIVED.format(n=position)

    return "Send a photo, or type *skip* / *done* to continue."


async def _finish_onboarding(session: Session, db: AsyncSession) -> str:
    await _persist_profile(session, db)
    user_id = UUID(session.user_id)
    await user_service.mark_onboarding_complete(db, user_id)

    # Generate embedding for matching (non-blocking failure is ok)
    try:
        from src.services.qdrant_service import upsert_profile
        await upsert_profile(user_id, session.profile_data)
    except Exception as e:
        logger.warning("Failed to generate embedding (non-fatal): %s", e)

    session.state = ConversationState.PROFILE_COMPLETE.value
    return msg.ONBOARDING_COMPLETE


async def _handle_complete_profile(session: Session, text_lower: str, db: AsyncSession) -> str:
    if text_lower in {"show matches", "matches", "browse", "find matches"}:
        session.state = ConversationState.BROWSING.value
        session.batch_number = 0
        session.data["shown_ids"] = []
        return await _show_matches(session, db)

    return msg.HELP_TEXT


async def _handle_browsing(session: Session, text_lower: str, db: AsyncSession) -> str:
    if text_lower in {"stop", "quit", "exit"}:
        session.state = ConversationState.PROFILE_COMPLETE.value
        return "Done browsing! Type *show matches* anytime to come back."

    if text_lower in {"more", "next", "show more"}:
        return await _show_matches(session, db)

    # Handle like/pass commands
    if text_lower.startswith("like") or text_lower.startswith("pass"):
        return await _handle_action(session, text_lower, db)

    return msg.MATCH_BATCH_FOOTER


async def _show_matches(session: Session, db: AsyncSession) -> str:
    from src.services.matching_service import get_matches

    user_id = UUID(session.user_id)
    exclude_ids = session.shown_ids

    matches = await get_matches(db, user_id, batch_size=5, exclude_ids=exclude_ids)

    if not matches:
        session.state = ConversationState.PROFILE_COMPLETE.value
        return msg.NO_MORE_MATCHES if session.batch_number > 0 else msg.NO_MATCHES

    session.batch_number += 1
    batch_data = []
    cards = [msg.MATCH_BATCH_HEADER]

    for i, match in enumerate(matches, 1):
        bio_highlight = ""
        bio = match.get("bio_prompts", {})
        if bio:
            first_key = next(iter(bio), None)
            if first_key:
                bio_highlight = f"💬 _{bio[first_key]}_"

        interests_str = ", ".join(match.get("interests", [])[:5])

        card = msg.MATCH_CARD.format(
            index=i,
            name=match.get("name", "Anonymous"),
            age=match.get("age", "?"),
            location=match.get("location", "Unknown"),
            relationship_type=match.get("relationship_type", ""),
            interests=interests_str or "Not specified",
            bio_highlight=bio_highlight,
        )
        cards.append(card)
        batch_data.append({
            "index": i,
            "user_id": match["id"],
            "name": match.get("name", "Anonymous"),
        })

    cards.append(msg.MATCH_BATCH_FOOTER)

    session.current_batch = batch_data
    session.add_shown_ids([m["user_id"] for m in batch_data])
    session.state = ConversationState.AWAITING_ACTION.value

    return "\n".join(cards)


async def _handle_action(session: Session, text_lower: str, db: AsyncSession) -> str:
    from src.services.matching_service import record_interaction, check_mutual_match

    parts = text_lower.split()
    action = parts[0]  # "like" or "pass"
    batch = session.current_batch

    if not batch:
        return "No profiles to act on. Type *show matches* to browse."

    # "like all" / "pass all"
    if len(parts) > 1 and parts[1] == "all":
        responses = []
        for item in batch:
            target_id = UUID(item["user_id"])
            user_id = UUID(session.user_id)
            await record_interaction(db, user_id, target_id, action)
            if action == "like":
                responses.append(msg.LIKED.format(name=item["name"]))
                mutual = await check_mutual_match(db, user_id, target_id)
                if mutual:
                    responses.append(mutual)
            else:
                responses.append(msg.PASSED.format(name=item["name"]))

        session.state = ConversationState.BROWSING.value
        responses.append("\nType *more* for next batch or *stop* to finish.")
        return "\n".join(responses)

    # "like 2" / "pass 3"
    if len(parts) > 1:
        try:
            idx = int(parts[1])
            item = next((b for b in batch if b["index"] == idx), None)
            if not item:
                return f"No profile #{idx} in current batch. Pick 1-{len(batch)}."

            target_id = UUID(item["user_id"])
            user_id = UUID(session.user_id)
            await record_interaction(db, user_id, target_id, action)

            if action == "like":
                response = msg.LIKED.format(name=item["name"])
                mutual = await check_mutual_match(db, user_id, target_id)
                if mutual:
                    response += "\n\n" + mutual
            else:
                response = msg.PASSED.format(name=item["name"])

            return response + "\n\nType *more* for next batch or *stop* to finish."
        except ValueError:
            pass

    return "Use: *like 1*, *pass 2*, *like all*, *pass all*, *more*, or *stop*."


async def _show_profile(session: Session, db: AsyncSession) -> str:
    user_id = UUID(session.user_id)
    user = await user_service.get_user(db, user_id)
    if not user:
        return "Profile not found."

    photos = await photo_service.get_photos(db, user_id)
    interests_str = ", ".join(user.interests or [])

    return msg.PROFILE_SUMMARY.format(
        name=user.name or "Not set",
        age=user.age or "Not set",
        gender=user.gender or "Not set",
        location=user.location or "Not set",
        relationship_type=user.relationship_type or "Not set",
        interests=interests_str or "Not set",
        photo_count=len(photos),
    )


async def _persist_profile(session: Session, db: AsyncSession) -> None:
    """Write accumulated profile_data from session to database."""
    user_id = UUID(session.user_id)
    pd = session.profile_data

    update_data = {}
    for key in ["name", "age", "gender", "location", "relationship_type"]:
        if key in pd:
            update_data[key] = pd[key]
    for key in ["bio_prompts", "preferences", "lifestyle", "values_data"]:
        if key in pd:
            update_data[key] = pd[key]
    if "interests" in pd:
        update_data["interests"] = pd["interests"]

    update_data["onboarding_step"] = session.question_index

    if update_data:
        await user_service.update_profile(db, user_id, update_data)
