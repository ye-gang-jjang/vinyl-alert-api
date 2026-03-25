from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories import releases as release_repository
from services.serializers import to_release_dict, to_release_summary_dict


def get_releases(db: Session):
    releases = release_repository.list_releases(db)
    return [to_release_dict(release, db) for release in releases]


def get_release_summaries(db: Session):
    releases = release_repository.list_releases(db)
    return [to_release_summary_dict(release, db) for release in releases]


def get_artist_release_summaries(db: Session, artist_name: str):
    releases = release_repository.list_artist_releases(db, artist_name)
    return [to_release_summary_dict(release, db) for release in releases]


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
