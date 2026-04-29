from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, load_only, selectinload

from models import Listing, Release


def list_releases(db: Session):
    return db.query(Release).order_by(Release.id.desc()).all()


def list_releases_for_matching(db: Session):
    return (
        db.query(Release)
        .options(load_only(Release.id, Release.artist_name, Release.album_title, Release.cover_image_url))
        .order_by(Release.id.desc())
        .all()
    )


def list_artist_releases(db: Session, artist_name: str):
    return (
        db.query(Release)
        .filter(Release.artist_name == artist_name)
        .order_by(Release.id.desc())
        .all()
    )


def list_artist_names(db: Session):
    rows = db.query(Release.artist_name).distinct().order_by(Release.artist_name.asc()).all()
    return [artist_name for artist_name, in rows]


def list_release_summaries_page(
    db: Session,
    page: int,
    page_size: int,
    artist_name: Optional[str] = None,
    store_slug: Optional[str] = None,
    sort: str = "default",
):
    filtered_query = db.query(Release)

    if artist_name:
        filtered_query = filtered_query.filter(Release.artist_name == artist_name)

    if store_slug:
        release_ids_for_store = (
            db.query(Listing.release_id)
            .filter(Listing.source_slug == store_slug)
            .subquery()
        )
        filtered_query = filtered_query.filter(Release.id.in_(release_ids_for_store))

    total = filtered_query.count()

    if sort == "artist_asc":
        ordered_query = filtered_query.order_by(Release.artist_name.asc(), Release.id.desc())
    elif sort == "album_asc":
        ordered_query = filtered_query.order_by(Release.album_title.asc(), Release.id.desc())
    else:
        ordered_query = (
            filtered_query.outerjoin(Listing)
            .group_by(Release.id)
            .order_by(func.max(Listing.collected_at).desc(), Release.id.desc())
        )

    releases = (
        ordered_query.options(selectinload(Release.listings))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return releases, total


def list_release_options_page(
    db: Session,
    page: int,
    page_size: int,
    sort: str = "default",
):
    filtered_query = db.query(Release)
    total = filtered_query.count()

    if sort == "artist_asc":
        ordered_query = filtered_query.order_by(Release.artist_name.asc(), Release.id.desc())
    elif sort == "album_asc":
        ordered_query = filtered_query.order_by(Release.album_title.asc(), Release.id.desc())
    else:
        ordered_query = (
            filtered_query.outerjoin(Listing)
            .group_by(Release.id)
            .order_by(func.max(Listing.collected_at).desc(), Release.id.desc())
        )

    releases = (
        ordered_query.options(load_only(Release.id, Release.artist_name, Release.album_title, Release.cover_image_url))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return releases, total


def get_release_by_id(db: Session, release_id: int):
    return db.query(Release).filter(Release.id == release_id).first()


def create_release(
    db: Session,
    artist_name: str,
    album_title: str,
    cover_image_url: Optional[str],
    *,
    commit: bool = True,
):
    release = Release(
        artist_name=artist_name,
        album_title=album_title,
        cover_image_url=cover_image_url,
    )
    db.add(release)
    if commit:
        db.commit()
        db.refresh(release)
    else:
        db.flush()
    return release


def fill_release_cover_image_if_missing(
    db: Session,
    release: Release,
    cover_image_url: Optional[str],
    *,
    commit: bool = True,
):
    if release.cover_image_url or not cover_image_url:
        return release

    release.cover_image_url = cover_image_url
    db.add(release)
    if commit:
        db.commit()
        db.refresh(release)
    else:
        db.flush()
    return release


def increment_release_view_count(db: Session, release: Release):
    release.view_count += 1
    db.add(release)
    db.commit()
    db.refresh(release)
    return release


def delete_release(db: Session, release: Release):
    db.delete(release)
    db.commit()
