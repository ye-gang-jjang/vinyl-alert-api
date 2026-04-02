from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories import releases as release_repository
from services.serializers import to_release_dict, to_release_summary_dict

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


def _normalize_page(page: int | None) -> int:
    if page is None or page < 1:
        return 1
    return page


def _normalize_page_size(page_size: int | None) -> int:
    if page_size is None or page_size < 1:
        return DEFAULT_PAGE_SIZE
    return min(page_size, MAX_PAGE_SIZE)


def _sort_release_summaries(releases: list, sort: str):
    if sort == "artist_asc":
        return sorted(releases, key=lambda release: release.artistName)

    if sort == "album_asc":
        return sorted(releases, key=lambda release: release.albumTitle)

    return sorted(
        releases,
        key=lambda release: release.latestCollectedAt or "",
        reverse=True,
    )


def _paginate_release_summaries(
    releases: list,
    page: int,
    page_size: int,
    artist_name: str | None = None,
    store_slug: str | None = None,
    sort: str = "default",
):
    filtered = releases

    if artist_name:
        filtered = [release for release in filtered if release.artistName == artist_name]

    if store_slug:
        filtered = [
            release
            for release in filtered
            if any(store.slug == store_slug for store in release.stores)
        ]

    sorted_releases = _sort_release_summaries(filtered, sort)
    total = len(sorted_releases)
    total_pages = max(1, (total + page_size - 1) // page_size)
    safe_page = min(page, total_pages)
    start = (safe_page - 1) * page_size
    end = start + page_size

    return {
        "items": sorted_releases[start:end],
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
    page: int | None = None,
    page_size: int | None = None,
    artist_name: str | None = None,
    store_slug: str | None = None,
    sort: str = "default",
):
    releases = release_repository.list_releases(db)
    summaries = [to_release_summary_dict(release, db) for release in releases]
    artists = sorted({summary.artistName for summary in summaries})

    stores_by_slug = {}
    for summary in summaries:
        for store in summary.stores:
            stores_by_slug[store.slug] = store

    paginated = _paginate_release_summaries(
        summaries,
        page=_normalize_page(page),
        page_size=_normalize_page_size(page_size),
        artist_name=artist_name,
        store_slug=store_slug,
        sort=sort,
    )
    paginated["artists"] = artists
    paginated["stores"] = sorted(stores_by_slug.values(), key=lambda store: store.name)
    return paginated


def get_artist_release_summaries(
    db: Session,
    artist_name: str,
    page: int | None = None,
    page_size: int | None = None,
):
    releases = release_repository.list_artist_releases(db, artist_name)
    summaries = [to_release_summary_dict(release, db) for release in releases]

    stores_by_slug = {}
    for summary in summaries:
        for store in summary.stores:
            stores_by_slug[store.slug] = store

    paginated = _paginate_release_summaries(
        summaries,
        page=_normalize_page(page),
        page_size=_normalize_page_size(page_size),
        artist_name=None,
        store_slug=None,
    )
    paginated["artists"] = [artist_name]
    paginated["stores"] = sorted(stores_by_slug.values(), key=lambda store: store.name)
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


def delete_release(db: Session, release_id: str):
    try:
        rid = int(release_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid release id")

    release = release_repository.get_release_by_id(db, rid)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    if release.listings and len(release.listings) > 0:
        raise HTTPException(
            status_code=400,
            detail="먼저 해당 릴리즈의 판매처를 삭제해 주세요.",
        )

    release_repository.delete_release(db, release)
