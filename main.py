# =========================
# Imports
# =========================
import os
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Release, Listing, Store


# =========================
# App
# =========================
app = FastAPI(title="Vinyl Alert API")


# =========================
# Middleware (CORS)
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
    storeSlug: str
    sourceProductTitle: str
    url: str


class StoreIn(BaseModel):
    name: str
    slug: str
    iconUrl: str  # 프론트 camelCase 유지


# =========================
# Response Serialization
# =========================
def to_release_dict(r: Release, db: Session):
    listings = []

    latest_collected_at: Optional[str] = None
    if r.listings:
        latest_collected_at = max(l.collected_at for l in r.listings).isoformat()

    for l in r.listings:
        store_name = ""
        store_icon = ""

        # ✅ storeSlug로 stores 조회해서 name/icon 구성
        s = db.query(Store).filter(Store.slug == l.source_slug).first()
        if s:
            store_name = s.name
            store_icon = s.icon_url

        listings.append(
            {
                "id": str(l.id),
                "sourceName": store_name,
                "sourceProductTitle": l.source_product_title,
                "url": l.url,
                "collectedAt": l.collected_at.isoformat(),
                "imageUrl": store_icon,
            }
        )

    return {
        "id": str(r.id),
        "artistName": r.artist_name,
        "albumTitle": r.album_title,
        "coverImageUrl": r.cover_image_url,
        "latestCollectedAt": latest_collected_at,
        "storesCount": len(listings),
        "listings": listings,
    }


# =========================
# Routes
# =========================
@app.get("/health")
def health_check():
    return {"status": "ok"}


# -------- Releases --------
@app.get("/releases")
def get_releases(db: Session = Depends(get_db)):
    releases = db.query(Release).order_by(Release.id.desc()).all()
    return [to_release_dict(r, db) for r in releases]


@app.get("/releases/{release_id}")
def get_release_by_id(release_id: str, db: Session = Depends(get_db)):
    try:
        rid = int(release_id)
    except ValueError:
        return None

    r = db.query(Release).filter(Release.id == rid).first()
    if not r:
        return None

    return to_release_dict(r, db)


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
    return to_release_dict(r, db)


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

    store = db.query(Store).filter(Store.slug == payload.storeSlug).first()
    if not store:
        raise HTTPException(status_code=400, detail="존재하지 않는 스토어입니다.")

    l = Listing(
        release_id=r.id,
        source_slug=store.slug,
        source_product_title=payload.sourceProductTitle,
        url=payload.url,
    )

    db.add(l)
    db.commit()
    db.refresh(r)

    return to_release_dict(r, db)


# -------- Stores --------
@app.get("/stores")
def get_stores(db: Session = Depends(get_db)):
    stores = db.query(Store).order_by(Store.name.asc()).all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "slug": s.slug,
            "iconUrl": s.icon_url,
        }
        for s in stores
    ]


@app.post("/stores")
def create_store(payload: StoreIn, db: Session = Depends(get_db)):
    exists = db.query(Store).filter(Store.slug == payload.slug).first()
    if exists:
        raise HTTPException(status_code=400, detail="slug already exists")

    store = Store(
        name=payload.name,
        slug=payload.slug,
        icon_url=payload.iconUrl,
    )

    db.add(store)
    db.commit()
    db.refresh(store)

    return {
        "id": str(store.id),
        "name": store.name,
        "slug": store.slug,
        "iconUrl": store.icon_url,
    }
