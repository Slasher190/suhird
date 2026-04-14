import logging
import shutil
from pathlib import Path
from uuid import UUID

from PIL import Image
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import Photo

logger = logging.getLogger("suhird.photo_service")

MAX_SIZE = 1024
JPEG_QUALITY = 85


def _get_photo_dir(user_id: UUID) -> Path:
    photo_dir = Path(settings.local_storage_path) / str(user_id)
    photo_dir.mkdir(parents=True, exist_ok=True)
    return photo_dir


def _process_image(input_path: Path, output_path: Path) -> None:
    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
        img.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)


async def upload_photo(
    db: AsyncSession, user_id: UUID, file_content: bytes, position: int
) -> Photo:
    photo_dir = _get_photo_dir(user_id)
    filename = f"photo_{position}.jpg"
    file_path = photo_dir / filename

    temp_path = photo_dir / f"_temp_{filename}"
    temp_path.write_bytes(file_content)

    try:
        _process_image(temp_path, file_path)
    finally:
        temp_path.unlink(missing_ok=True)

    # Upsert: delete existing photo at this position, then create new
    await db.execute(
        delete(Photo).where(Photo.user_id == user_id, Photo.position == position)
    )

    relative_path = f"{user_id}/{filename}"
    photo = Photo(user_id=user_id, file_path=relative_path, position=position)
    db.add(photo)
    await db.flush()
    await db.refresh(photo)
    logger.info("Uploaded photo %d for user %s", position, user_id)
    return photo


def get_photo_url(user_id: UUID, position: int) -> str:
    return f"/photos/{user_id}/photo_{position}.jpg"


def get_all_photo_urls(user_id: UUID, photos: list[Photo]) -> list[str]:
    return [get_photo_url(user_id, p.position) for p in sorted(photos, key=lambda p: p.position)]


async def delete_photo(db: AsyncSession, user_id: UUID, position: int) -> bool:
    result = await db.execute(
        select(Photo).where(Photo.user_id == user_id, Photo.position == position)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        return False

    file_path = Path(settings.local_storage_path) / photo.file_path
    file_path.unlink(missing_ok=True)

    await db.delete(photo)
    await db.flush()
    return True


async def get_photos(db: AsyncSession, user_id: UUID) -> list[Photo]:
    result = await db.execute(
        select(Photo).where(Photo.user_id == user_id).order_by(Photo.position)
    )
    return list(result.scalars().all())
