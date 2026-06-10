from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from repositories import stores as store_repository
from models import Store
from schemas.listings import ListingOut
from schemas.releases import ReleaseOut, ReleaseSummaryOut
from schemas.stores import StoreRefOut


def serialize_dt(dt: Any) -> Optional[str]:
    if dt is None or not isinstance(dt, datetime):
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _listing_out_from_store(listing, store: Optional[Store]):
    store_name = ""
    store_icon = ""

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
    )


def to_listing_dict_with_store_map(listing, store_map: dict[str, Store]):
    return _listing_out_from_store(listing, store_map.get(str(listing.source_slug)))


def to_release_dict(release, db: Session):
    slugs = [str(listing.source_slug) for listing in release.listings if listing.source_slug is not None]
    stores = store_repository.get_stores_by_slugs(db, slugs)
    store_map = {str(store.slug): store for store in stores}
    return to_release_dict_with_store_map(release, store_map)


def to_release_dict_with_store_map(release, store_map: dict[str, Store]):
    latest_collected_at = None
    if release.listings:
        latest_collected_at = serialize_dt(max(listing.collected_at for listing in release.listings))

    sorted_listings = sorted(
        release.listings,
        key=lambda listing: -listing.collected_at.timestamp(),
    )

    return ReleaseOut(
        id=str(release.id),
        artistName=release.artist_name,
        albumTitle=release.album_title,
        coverImageUrl=release.cover_image_url,
        viewCount=release.view_count,
        latestCollectedAt=latest_collected_at,
        storesCount=len(sorted_listings),
        listings=[to_listing_dict_with_store_map(listing, store_map) for listing in sorted_listings],
        collectedAt=serialize_dt(getattr(release, "created_at", None)),
    )


def to_release_summary_with_store_map(release, store_map: dict[str, Store]):
    latest_collected_at = None
    if release.listings:
        latest_collected_at = serialize_dt(max(listing.collected_at for listing in release.listings))

    slugs = sorted({str(listing.source_slug) for listing in release.listings if listing.source_slug is not None})
    store_refs = []

    for slug in slugs:
        store = store_map.get(slug)
        if store:
            store_refs.append(
                StoreRefOut(
                    slug=str(store.slug),
                    name=store.name,
                    iconUrl=store.icon_url,
                )
            )
        else:
            store_refs.append(StoreRefOut(slug=slug, name=slug, iconUrl=""))

    return ReleaseSummaryOut(
        id=str(release.id),
        artistName=release.artist_name,
        albumTitle=release.album_title,
        coverImageUrl=release.cover_image_url,
        viewCount=release.view_count,
        latestCollectedAt=latest_collected_at,
        storesCount=len(store_refs),
        stores=store_refs,
        collectedAt=serialize_dt(getattr(release, "created_at", None)),
    )
