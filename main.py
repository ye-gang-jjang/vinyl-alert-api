import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from db import engine, SessionLocal
from models import Base, Release, Listing

from store_icons import get_store_icon_url

# ✅ 앱 시작 시 테이블 생성 (없으면 생성, 있으면 패스)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vinyl Alert API")


# --------------------
# ✅ CORS (환경변수 기반)
# --------------------
def get_allowed_origins():
    raw = os.getenv("ALLOW_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]

ALLOWED_ORIGINS = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ DB 세션 dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------
# 입력용 스키마 (Admin -> API)
# --------------------
class ReleaseIn(BaseModel):
    artistName: str
    albumTitle: str
    color: Optional[str] = None
    format: Optional[str] = None
    coverImageUrl: Optional[str] = None


class ListingIn(BaseModel):
    sourceName: str
    sourceProductTitle: str
    url: str
    collectedAgo: str  # MVP에서는 표시용(저장은 collected_at)
    imageUrl: Optional[str] = None


# --------------------
# 모델 -> 응답 변환 (프론트가 쓰는 형태)
# --------------------
def to_release_dict(r: Release):
    listings = []
    for l in r.listings:
        listings.append(
            {
                "id": str(l.id),
                "sourceName": l.source_name,
                "sourceProductTitle": l.source_product_title,
                "url": l.url,
                "collectedAgo": "just now",
                "imageUrl": l.image_url,
            }
        )

    return {
        "id": str(r.id),
        "artistName": r.artist_name,
        "albumTitle": r.album_title,
        "color": r.color,
        "format": r.format,
        "coverImageUrl": r.cover_image_url,
        "latestCollectedAgo": "just now",
        "storesCount": len(listings),
        "listings": listings,
    }


# --------------------
# API
# --------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/releases")
def get_releases(db: Session = Depends(get_db)):
    releases = db.query(Release).order_by(Release.id.desc()).all()
    return [to_release_dict(r) for r in releases]


@app.get("/releases/{release_id}")
def get_release_by_id(release_id: str, db: Session = Depends(get_db)):
    try:
        rid = int(release_id)
    except ValueError:
        return None

    r = db.query(Release).filter(Release.id == rid).first()
    if not r:
        return None
    return to_release_dict(r)


@app.post("/releases")
def create_release(payload: ReleaseIn, db: Session = Depends(get_db)):
    r = Release(
        artist_name=payload.artistName,
        album_title=payload.albumTitle,
        color=payload.color,
        format=payload.format,
        cover_image_url=payload.coverImageUrl,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return to_release_dict(r)


@app.post("/releases/{release_id}/listings")
def add_listing(release_id: str, payload: ListingIn, db: Session = Depends(get_db)):
    try:
        rid = int(release_id)
    except ValueError:
        return None

    r = db.query(Release).filter(Release.id == rid).first()
    if not r:
        return None

    l = Listing(
        release_id=r.id,
        source_name=payload.sourceName,
        source_product_title=payload.sourceProductTitle,
        url=payload.url,
        image_url=get_store_icon_url(payload.sourceName),
    )

    db.add(l)
    db.commit()
    db.refresh(r)
    return to_release_dict(r)
