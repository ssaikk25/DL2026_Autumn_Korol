"""SQLAlchemy ORM models."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime (SQLite-compatible)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MemeCategory(str, enum.Enum):
    hot = "hot"
    cold = "cold"
    rain = "rain"
    snow = "snow"
    wind = "wind"
    comfort = "comfort"


class Vote(str, enum.Enum):
    up = "up"
    down = "down"


class Meme(Base):
    __tablename__ = "memes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[MemeCategory] = mapped_column(Enum(MemeCategory), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="rumeme-desc")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    stats: Mapped["MemeStats"] = relationship(
        back_populates="meme", uselist=False, cascade="all, delete-orphan"
    )


class MemeStats(Base):
    __tablename__ = "meme_stats"

    meme_id: Mapped[int] = mapped_column(ForeignKey("memes.id"), primary_key=True)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    dislikes: Mapped[int] = mapped_column(Integer, default=0)
    alpha: Mapped[float] = mapped_column(Float, default=1.0)
    beta: Mapped[float] = mapped_column(Float, default=1.0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    meme: Mapped["Meme"] = relationship(back_populates="stats")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meme_id: Mapped[int] = mapped_column(ForeignKey("memes.id"), index=True)
    vote: Mapped[Vote] = mapped_column(Enum(Vote), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    weather_context: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class WeatherCache(Base):
    __tablename__ = "weather_cache"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[float] = mapped_column(Float, default=0.0)
