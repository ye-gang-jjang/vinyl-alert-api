from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from repositories import stores as store_repository
from schemas.listings import ListingOut
from schemas.releases import ReleaseOut, ReleaseSummaryOut
from schemas.stores import StoreRefOut


def serialize_dt(dt: Any) -> Optional[str]:
    if dt is None or not isinstance(dt, datetime):
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def to_listing_dict(listing, db: Session):
    store_name = ""
    store_icon = ""

    store = store_repository.get_store_by_slug(db, listing.source_slug)
    if store:
        store_name = store.name
        store_icon = store.icon_url

    return ListingOut(
        id=str(listing.id),
        sourceName=store_name,
        sourceProductTitle=listing.source_product_title,
        url=listing.url,
        collectedAt=serialize_dt(listing.collected_at),
        imageUrl=store_icon,
        latestCollectedAt=None,
        price=listing.price,
        status=listing.status,
    )


def to_release_dict(release, db: Session):
    latest_collected_at = None
    if release.listings:
        latest_collected_at = serialize_dt(max(listing.collected_at for listing in release.listings))

    status_priority: dict[str, int] = {"PREORDER": 0, "ON_SALE": 1, "SOLD_OUT": 2}
    sorted_listings = sorted(
        release.listings,
        key=lambda listing: (
            status_priority.get(str(getattr(listing, "status", "")), 99),
            -listing.collected_at.timestamp(),
        ),
    )

    return ReleaseOut(
        id=str(release.id),
        artistName=release.artist_name,
        albumTitle=release.album_title,
        coverImageUrl=release.cover_image_url,
        latestCollectedAt=latest_collected_at,
        storesCount=len(sorted_listings),
        listings=[to_listing_dict(listing, db) for listing in sorted_listings],
        collectedAt=serialize_dt(getattr(release, "created_at", None)),
    )


def to_release_summary_dict(release, db: Session):
    latest_collected_at = None
    if release.listings:
        latest_collected_at = serialize_dt(max(listing.collected_at for listing in release.listings))

    slugs = list({str(listing.source_slug) for listing in release.listings if listing.source_slug is not None})
    stores = store_repository.get_stores_by_slugs(db, slugs)
    store_refs = sorted(
        [
            StoreRefOut(
                slug=str(store.slug),
                name=store.name,
                iconUrl=store.icon_url,
            )
            for store in stores
        ],
        key=lambda store: store.name,
    )

    if not store_refs:
        fallback_names = sorted({str(listing.source_slug) for listing in release.listings})
        store_refs = [
            StoreRefOut(slug=name, name=name, iconUrl="")
            for name in fallback_names
        ]
    elif len(store_refs) < len(slugs):
        known_slugs = {store.slug for store in store_refs}
        missing_slugs = sorted([slug for slug in slugs if slug not in known_slugs])
        store_refs.extend(
            [StoreRefOut(slug=slug, name=slug, iconUrl="") for slug in missing_slugs]
        )

    return ReleaseSummaryOut(
        id=str(release.id),
        artistName=release.artist_name,
        albumTitle=release.album_title,
        coverImageUrl=release.cover_image_url,
        latestCollectedAt=latest_collected_at,
        storesCount=len(store_refs),
        stores=store_refs,
        collectedAt=serialize_dt(getattr(release, "created_at", None)),
    )
