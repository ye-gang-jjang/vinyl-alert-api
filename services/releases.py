from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories import listings as listing_repository
from repositories import releases as release_repository
from repositories import stores as store_repository
from schemas.stores import StoreRefOut
from services.serializers import to_release_dict, to_release_summary_with_store_map

DEFAULT_PAGE_SIZE = 18
MAX_PAGE_SIZE = 100


def _normalize_page(page: Optional[int]) -> int:
    if page is None or page < 1:
        return 1
    return page


def _normalize_page_size(page_size: Optional[int]) -> int:
    if page_size is None or page_size < 1:
        return DEFAULT_PAGE_SIZE
    return min(page_size, MAX_PAGE_SIZE)


def _build_paginated_payload(
    releases: list,
    total: int,
    page: int,
    page_size: int,
):
    total_pages = max(1, (total + page_size - 1) // page_size)
    safe_page = min(page, total_pages)

    return {
        "items": releases,
        "page": safe_page,
        "pageSize": page_size,
        "total": total,
        "totalPages": total_pages,
    }


def get_releases(db: Session):
    releases = release_repository.list_releases(db)
    return [to_release_dict(release, db) for release in releases]


def get_release_summaries(
    db: Session,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    artist_name: Optional[str] = None,
    store_slug: Optional[str] = None,
    sort: str = "default",
):
    safe_page = _normalize_page(page)
    safe_page_size = _normalize_page_size(page_size)
    stores = store_repository.list_stores(db)
    store_map = {str(store.slug): store for store in stores}
    releases, total = release_repository.list_release_summaries_page(
        db,
        page=safe_page,
        page_size=safe_page_size,
        artist_name=artist_name,
        store_slug=store_slug,
        sort=sort,
    )
    summaries = [to_release_summary_with_store_map(release, store_map) for release in releases]

    paginated = _build_paginated_payload(
        summaries,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )
    paginated["artists"] = release_repository.list_artist_names(db)
    paginated["stores"] = [
        StoreRefOut(
            slug=str(store.slug),
            name=store.name,
            iconUrl=store.icon_url,
        )
        for store in stores
    ]
    return paginated


def get_artist_release_summaries(
    db: Session,
    artist_name: str,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
):
    safe_page = _normalize_page(page)
    safe_page_size = _normalize_page_size(page_size)
    stores = store_repository.list_stores(db)
    store_map = {str(store.slug): store for store in stores}
    releases, total = release_repository.list_release_summaries_page(
        db,
        page=safe_page,
        page_size=safe_page_size,
        artist_name=artist_name,
    )
    summaries = [to_release_summary_with_store_map(release, store_map) for release in releases]

    paginated = _build_paginated_payload(
        summaries,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )
    paginated["artists"] = [artist_name]
    paginated["stores"] = [
        StoreRefOut(
            slug=str(store.slug),
            name=store.name,
            iconUrl=store.icon_url,
        )
        for store in stores
    ]
    return paginated


def get_release_by_id(db: Session, release_id: str):
    try:
        rid = int(release_id)
    except ValueError:
        return None

    release = release_repository.get_release_by_id(db, rid)
    if not release:
        return None

    return to_release_dict(release, db)


def create_release(db: Session, payload):
    release = release_repository.create_release(
        db,
        artist_name=payload.artistName,
        album_title=payload.albumTitle,
        cover_image_url=payload.coverImageUrl,
    )
    return to_release_dict(release, db)


def record_release_view(db: Session, release_id: str):
    try:
        rid = int(release_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid release id")

    release = release_repository.get_release_by_id(db, rid)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    release = release_repository.increment_release_view_count(db, release)
    return {
        "id": str(release.id),
        "viewCount": release.view_count,
    }


def delete_release(db: Session, release_id: str):
    try:
        rid = int(release_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid release id")

    release = release_repository.get_release_by_id(db, rid)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    if listing_repository.exists_listing_by_release_id(db, release.id):
        raise HTTPException(
            status_code=400,
            detail="먼저 해당 릴리즈의 판매처를 삭제해 주세요.",
        )

    release_repository.delete_release(db, release)
