from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories import listings as listing_repository
from repositories import stores as store_repository
from schemas.stores import StoreOut, StoreWithCountOut


def get_stores(db: Session):
    stores = store_repository.list_stores(db)

    return [
        StoreWithCountOut(
            id=str(store.id),
            name=store.name,
            slug=store.slug,
            iconUrl=store.icon_url,
            listingsCount=listing_repository.count_listings_by_store_slug(db, str(store.slug)),
        )
        for store in stores
    ]


def create_store(db: Session, payload):
    existing_store = store_repository.get_store_by_slug(db, payload.slug)
    if existing_store:
        raise HTTPException(status_code=400, detail="slug already exists")

    store = store_repository.create_store(db, payload.name, payload.slug, payload.iconUrl)
    return StoreOut(
        id=str(store.id),
        name=store.name,
        slug=store.slug,
        iconUrl=store.icon_url,
    )


def delete_store(db: Session, store_id: str):
    try:
        sid = int(store_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid store id")

    store = store_repository.get_store_by_id(db, sid)
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    listing_count = listing_repository.count_listings_by_store_slug(db, str(store.slug))
    if listing_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"store is referenced by {listing_count} listings",
        )

    store_repository.delete_store(db, store)
