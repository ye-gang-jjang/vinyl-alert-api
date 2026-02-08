# =========================
# Imports
# =========================
import os
from typing import Optional, Literal
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Response
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
ListingStatus = Literal["ON_SALE", "PREORDER", "SOLD_OUT"]


class ReleaseIn(BaseModel):
    artistName: str
    albumTitle: str
    coverImageUrl: Optional[str] = None


class ListingIn(BaseModel):
    storeSlug: str
    sourceProductTitle: str
    url: str
    price: Optional[int] = None
    status: ListingStatus = "ON_SALE"


class ListingUpdate(BaseModel):
    price: Optional[int] = None
    status: Optional[ListingStatus] = None


class StoreIn(BaseModel):
    name: str
    slug: str
    iconUrl: str  # 프론트 camelCase 유지


# =========================
# Response Serialization
# =========================
def to_listing_dict(l: Listing, db: Session):
    store_name = ""
    store_icon = ""

    s = db.query(Store).filter(Store.slug == l.source_slug).first()
    if s:
        store_name = s.name
        store_icon = s.icon_url

    return {
        "id": str(l.id),
        "sourceName": store_name,
        "sourceProductTitle": l.source_product_title,
        "url": l.url,
        "collectedAt": l.collected_at.isoformat() if l.collected_at else None,
        "imageUrl": store_icon,
        "latestCollectedAt": None,  # 프론트 DTO 형식 맞춤(현재 미사용)
        "price": l.price,
        "status": l.status,
    }


def to_release_dict(r: Release, db: Session):
    # ✅ 최신 수집(=업데이트) 시각: listing들의 collected_at 중 가장 최근
    latest_collected_at: Optional[str] = None
    if r.listings:
        latest_collected_at = max(l.collected_at for l in r.listings).isoformat()

    # ✅ 정렬: PREORDER > ON_SALE > SOLD_OUT, 같은 상태면 최신(collected_at) 우선
    STATUS_PRIORITY = {"PREORDER": 0, "ON_SALE": 1, "SOLD_OUT": 2}

    sorted_listings = sorted(
        r.listings,
        key=lambda l: (
            STATUS_PRIORITY.get(getattr(l, "status", None), 99),
            -l.collected_at.timestamp(),
        ),
    )

    listings = [to_listing_dict(l, db) for l in sorted_listings]

    return {
        "id": str(r.id),
        "artistName": r.artist_name,
        "albumTitle": r.album_title,
        "coverImageUrl": r.cover_image_url,
        "latestCollectedAt": latest_collected_at,
        "storesCount": len(listings),
        "listings": listings,
        "collectedAt": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
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


@app.delete("/releases/{release_id}", status_code=204)
def delete_release(release_id: str, db: Session = Depends(get_db)):
    try:
        rid = int(release_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid release id")

    r = db.query(Release).filter(Release.id == rid).first()
    if not r:
        raise HTTPException(status_code=404, detail="Release not found")

    # 판매처가 남아 있으면 삭제 금지
    if r.listings and len(r.listings) > 0:
        raise HTTPException(
            status_code=400, detail="먼저 해당 릴리즈의 판매처를 삭제해 주세요."
        )

    db.delete(r)
    db.commit()
    return


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
        price=payload.price,
        status=payload.status,
    )

    db.add(l)
    db.commit()
    db.refresh(l)
    db.refresh(r)

    return to_release_dict(r, db)


@app.patch("/listings/{listing_id}")
def update_listing(listing_id: str, payload: ListingUpdate, db: Session = Depends(get_db)):
    try:
        lid = int(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid listing id")

    l = db.query(Listing).filter(Listing.id == lid).first()
    if not l:
        raise HTTPException(status_code=404, detail="Listing not found")

    fields = payload.model_fields_set

    changed = False  # ✅ 실제 변경 발생 여부

    if "status" in fields:
        if payload.status is None:
            raise HTTPException(status_code=400, detail="status cannot be null")

        if l.status != payload.status:
            l.status = payload.status
            changed = True

        if payload.status == "SOLD_OUT":
            if l.price is not None:
                l.price = None
                changed = True

    if "price" in fields:
        # price: null -> 지우기
        if payload.price is None:
            if l.price is not None:
                l.price = None
                changed = True
        else:
            if l.status != "SOLD_OUT":
                if l.price != payload.price:
                    l.price = payload.price
                    changed = True

    # ✅ “수집=업데이트” 정책: 변경이 있으면 collected_at을 최신으로 갱신
    if changed:
        l.collected_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(l)

    return to_listing_dict(l, db)


@app.delete("/listings/{listing_id}", status_code=204)
def delete_listing(listing_id: str, db: Session = Depends(get_db)):
    try:
        lid = int(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid listing id")

    l = db.query(Listing).filter(Listing.id == lid).first()
    if not l:
        raise HTTPException(status_code=404, detail="Listing not found")

    db.delete(l)
    db.commit()
    return


# -------- Stores --------
@app.get("/stores")
def get_stores(db: Session = Depends(get_db)):
    stores = db.query(Store).order_by(Store.name.asc()).all()

    result = []
    for s in stores:
        cnt = db.query(Listing).filter(Listing.source_slug == s.slug).count()

        result.append(
            {
                "id": str(s.id),
                "name": s.name,
                "slug": s.slug,
                "iconUrl": s.icon_url,
                "listingsCount": cnt,
            }
        )

    return result


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


@app.delete("/stores/{store_id}", status_code=204)
def delete_store(store_id: str, db: Session = Depends(get_db)):
    try:
        sid = int(store_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid store id")

    store = db.query(Store).filter(Store.id == sid).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    # ✅ 참조 listing 존재하면 삭제 금지
    cnt = db.query(Listing).filter(Listing.source_slug == store.slug).count()
    if cnt > 0:
        raise HTTPException(
            status_code=400,
            detail=f"store is referenced by {cnt} listings",
        )

    db.delete(store)
    db.commit()
    return Response(status_code=204)
