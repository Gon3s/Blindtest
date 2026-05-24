from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RoomModel(Base):
    __tablename__ = "rooms"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    host_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    host_token: Mapped[str] = mapped_column(String(64), nullable=False)
    config: Mapped[Any] = mapped_column(JSONB, nullable=False)


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False
    )


class ParticipantModel(Base):
    __tablename__ = "participants"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False
    )
    team_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    is_host: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class RoundModel(Base):
    __tablename__ = "rounds"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    answer_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="both"
    )


class SongModel(Base):
    __tablename__ = "songs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    artist: Mapped[str] = mapped_column(String(300), nullable=False)
    round_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rounds.id"), nullable=False
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    aliases_title: Mapped[Any] = mapped_column(JSONB, nullable=False)
    aliases_artist: Mapped[Any] = mapped_column(JSONB, nullable=False)
    preview_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AnswerModel(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint(
            "song_id", "participant_id", name="uq_answers_song_participant"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    song_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("songs.id"), nullable=False
    )
    participant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("participants.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    title_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    artist_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    host_override: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class ScoreEntryModel(Base):
    __tablename__ = "score_entries"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    participant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("participants.id"), nullable=False
    )
    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False
    )
    song_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("songs.id"), nullable=True
    )
    round_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rounds.id"), nullable=True
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)


class RoomEventModel(Base):
    __tablename__ = "room_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Any] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
