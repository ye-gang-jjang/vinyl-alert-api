from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    artist_name: Mapped[str] = mapped_column(String, nullable=False)
    album_title: Mapped[str] = mapped_column(String, nullable=False)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    listings = relationship(
        "Listing",
        back_populates="release",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
