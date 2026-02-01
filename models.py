from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    artist_name: Mapped[str] = mapped_column(String, index=True)
    album_title: Mapped[str] = mapped_column(String, index=True)

    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    listings: Mapped[list["Listing"]] = relationship(
        back_populates="release",
        cascade="all, delete-orphan",
    )


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id"), index=True)

    source_name: Mapped[str] = mapped_column(String)
    source_product_title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    release: Mapped["Release"] = relationship(back_populates="listings")
