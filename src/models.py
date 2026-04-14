import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_encrypted = Column(Text, nullable=False, unique=True)
    name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))
    location = Column(String(200))
    bio_prompts = Column(JSONB, default=dict)
    preferences = Column(JSONB, default=dict)
    lifestyle = Column(JSONB, default=dict)
    values_data = Column(JSONB, default=dict)
    interests = Column(ARRAY(Text), default=list)
    relationship_type = Column(String(50))
    onboarding_complete = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")
    sent_interactions = relationship("Interaction", foreign_keys="Interaction.user_id", back_populates="user", cascade="all, delete-orphan")
    received_interactions = relationship("Interaction", foreign_keys="Interaction.target_user_id", back_populates="target_user", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="photos")

    __table_args__ = (
        UniqueConstraint("user_id", "position"),
        CheckConstraint("position >= 1 AND position <= 6"),
    )


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", foreign_keys=[user_id], back_populates="sent_interactions")
    target_user = relationship("User", foreign_keys=[target_user_id], back_populates="received_interactions")

    __table_args__ = (
        UniqueConstraint("user_id", "target_user_id"),
        CheckConstraint("action IN ('like', 'pass')"),
    )


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_b_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    matched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])

    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id"),)


class Block(Base):
    __tablename__ = "blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blocked_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    blocker = relationship("User", foreign_keys=[blocker_id])
    blocked = relationship("User", foreign_keys=[blocked_id])

    __table_args__ = (UniqueConstraint("blocker_id", "blocked_id"),)
