from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class PendingCandidate(Base):
    __tablename__ = "pending_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    artist_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    album_title: Mapped[str] = mapped_column(String, nullable=False)
    source_slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_product_title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    matched_release_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("releases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
