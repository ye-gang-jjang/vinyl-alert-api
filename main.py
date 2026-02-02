# =========================
# Imports
# =========================
import os
from typing import Optional

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import engine, SessionLocal
from models import Base, Release, Listing
from store_icons import get_store_icon_url


# =========================
# App & DB bootstrap
# =========================
# ✅ 앱 시작 시 테이블 생성 (없으면 생성, 있으면 패스)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vinyl Alert API")


# =========================
# Middleware (CORS 등)
# =========================
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


# =========================
# Dependencies (get_db)
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# Pydantic Schemas (Request)
# =========================
class ReleaseIn(BaseModel):
    artistName: str
    albumTitle: str
    coverImageUrl: Optional[str] = None


class ListingIn(BaseModel):
    sourceName: str
    sourceProductTitle: str
    url: str
    collectedAgo: str  # MVP에서는 표시용(저장은 collected_at)
    imageUrl: Optional[str] = None


# (선택) 앞으로 Store 등록을 추가한다면 여기에 StoreIn/StoreOut 같은 스키마를 추가하거나,
# schemas.py로 빼는 게 더 깔끔함.


# =========================
# Response Serialization
# (모델 -> 프론트 응답 형태 변환)
# =========================
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
        "coverImageUrl": r.cover_image_url,
        "latestCollectedAgo": "just now",
        "storesCount": len(listings),
        "listings": listings,
    }


# =========================
# Routes (API)
# =========================
@app.get("/health")
def health_check():
    return {"status": "ok"}


# -------- Releases --------
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
        cover_image_url=payload.coverImageUrl,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return to_release_dict(r)


# -------- Listings --------
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


# -------- Stores (추가 예정) --------
# ✅ "스토어 등록"을 추가한다면, 라우터는 가장 아래에 붙이는 게 관리가 쉬움
# 예: @app.get("/stores"), @app.post("/stores")
