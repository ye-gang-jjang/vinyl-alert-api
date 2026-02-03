from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Release(Base):
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, index=True)

    artist_name = Column(String, nullable=False)
    album_title = Column(String, nullable=False)
    cover_image_url = Column(String, nullable=True)

    # ✅ created_at 기본값(권장: Release에도 통일)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계
    listings = relationship(
        "Listing",
        back_populates="release",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)

    release_id = Column(
        Integer,
        ForeignKey("releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # stores.slug 값을 참조(너 main.py에서 source_slug로 Store를 찾고 있음)
    source_slug = Column(String, nullable=False, index=True)

    source_product_title = Column(String, nullable=False)
    url = Column(String, nullable=False)

    # ✅ collected_at 기본값(리스트 추가 시 자동 기록)
    collected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ✅ created_at도 통일해서 넣고 싶으면 사용(선택)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계
    release = relationship("Release", back_populates="listings")


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True, index=True)
    icon_url = Column(String, nullable=False)

    # ✅ 핵심: created_at NOT NULL이면 반드시 기본값 필요
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
