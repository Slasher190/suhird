import base64
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from src.config import settings


def _get_fernet() -> Fernet:
    key = settings.encryption_key
    # Pad or hash the key to make it a valid Fernet key (32 url-safe base64 bytes)
    if len(key) < 32:
        key = key.ljust(32, "0")
    key_bytes = base64.urlsafe_b64encode(key[:32].encode())
    return Fernet(key_bytes)


def encrypt_phone(phone: str) -> str:
    f = _get_fernet()
    return f.encrypt(phone.encode()).decode()


def decrypt_phone(encrypted: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()


def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_jwt_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
