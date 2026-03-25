from typing import Optional

from sqlalchemy.orm import Session

from models import Release


def list_releases(db: Session):
    return db.query(Release).order_by(Release.id.desc()).all()


def list_artist_releases(db: Session, artist_name: str):
    return (
        db.query(Release)
        .filter(Release.artist_name == artist_name)
        .order_by(Release.id.desc())
        .all()
    )


def get_release_by_id(db: Session, release_id: int):
    return db.query(Release).filter(Release.id == release_id).first()


def create_release(
    db: Session,
    artist_name: str,
    album_title: str,
    cover_image_url: Optional[str],
):
    release = Release(
        artist_name=artist_name,
        album_title=album_title,
        cover_image_url=cover_image_url,
    )
    db.add(release)
    db.commit()
    db.refresh(release)
    return release


def delete_release(db: Session, release: Release):
    db.delete(release)
    db.commit()
