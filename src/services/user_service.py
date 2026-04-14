import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import User, Photo
from src.utils.security import encrypt_phone, decrypt_phone

logger = logging.getLogger("suhird.user_service")


async def create_user(db: AsyncSession, phone: str) -> User:
    encrypted = encrypt_phone(phone)
    user = User(phone_encrypted=encrypted)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("Created user %s", user.id)
    return user


async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(
        select(User).options(selectinload(User.photos)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    encrypted = encrypt_phone(phone)
    result = await db.execute(
        select(User).options(selectinload(User.photos)).where(User.phone_encrypted == encrypted)
    )
    return result.scalar_one_or_none()


async def update_profile(db: AsyncSession, user_id: UUID, data: dict) -> User | None:
    user = await get_user(db, user_id)
    if not user:
        return None
    for key, value in data.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user


async def mark_onboarding_complete(db: AsyncSession, user_id: UUID) -> User | None:
    user = await get_user(db, user_id)
    if not user:
        return None
    user.onboarding_complete = True
    await db.flush()
    await db.refresh(user)
    logger.info("User %s completed onboarding", user_id)
    return user


async def get_all_complete_users(db: AsyncSession, exclude_id: UUID | None = None) -> list[User]:
    stmt = select(User).options(selectinload(User.photos)).where(User.onboarding_complete == True)
    if exclude_id:
        stmt = stmt.where(User.id != exclude_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_user_phone(db: AsyncSession, user_id: UUID) -> str | None:
    user = await get_user(db, user_id)
    if not user:
        return None
    return decrypt_phone(user.phone_encrypted)


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    user = await get_user(db, user_id)
    if not user:
        return False
    await db.delete(user)
    await db.flush()
    logger.info("Deleted user %s", user_id)
    return True
