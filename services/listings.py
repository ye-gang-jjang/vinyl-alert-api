from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories import listings as listing_repository
from repositories import releases as release_repository
from repositories import stores as store_repository
from services.serializers import to_listing_dict_with_store_map, to_release_dict_with_store_map


def add_listing(db: Session, release_id: str, payload):
    try:
        rid = int(release_id)
    except ValueError:
        return None

    release = release_repository.get_release_by_id(db, rid)
    if not release:
        return None

    store = store_repository.get_store_by_slug(db, payload.storeSlug)
    if not store:
        raise HTTPException(status_code=400, detail="존재하지 않는 스토어입니다.")

    listing_repository.create_listing(
        db,
        release_id=release.id,
        source_slug=store.slug,
        source_product_title=payload.sourceProductTitle,
        url=payload.url,
        price=payload.price,
    )
    db.refresh(release)
    source_slugs = [str(item.source_slug) for item in release.listings if item.source_slug is not None]
    stores = store_repository.get_stores_by_slugs(db, source_slugs)
    store_map = {str(item.slug): item for item in stores}

    return to_release_dict_with_store_map(release, store_map)


def update_listing(db: Session, listing_id: str, payload):
    try:
        lid = int(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid listing id")

    listing = listing_repository.get_listing_by_id(db, lid)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    fields = payload.model_fields_set
    changed = False

    if "price" in fields:
        if payload.price is None:
            if listing.price is not None:
                listing.price = None
                changed = True
        elif listing.price != payload.price:
            listing.price = payload.price
            changed = True

    if changed:
        listing.collected_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(listing)

    store = store_repository.get_store_by_slug(db, listing.source_slug)
    store_map = {str(store.slug): store} if store else {}

    return to_listing_dict_with_store_map(listing, store_map)


def delete_listing(db: Session, listing_id: str):
    try:
        lid = int(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid listing id")

    listing = listing_repository.get_listing_by_id(db, lid)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing_repository.delete_listing(db, listing)
