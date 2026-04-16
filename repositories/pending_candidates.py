from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models import PendingCandidate


def list_pending_candidates(
    db: Session,
    *,
    status: Optional[str] = None,
    source_slug: Optional[str] = None,
    query: Optional[str] = None,
):
    candidates = db.query(PendingCandidate)

    if status:
        candidates = candidates.filter(PendingCandidate.status == status)
    if source_slug:
        candidates = candidates.filter(PendingCandidate.source_slug == source_slug)
    if query:
        keyword = f"%{query}%"
        candidates = candidates.filter(
            or_(
                PendingCandidate.artist_name.ilike(keyword),
                PendingCandidate.album_title.ilike(keyword),
                PendingCandidate.source_product_title.ilike(keyword),
            )
        )

    return candidates.order_by(PendingCandidate.status.asc(), PendingCandidate.created_at.desc()).all()


def get_pending_candidate_by_id(db: Session, candidate_id: int):
    return db.query(PendingCandidate).filter(PendingCandidate.id == candidate_id).first()


def get_pending_candidate_by_url(db: Session, url: str):
    return db.query(PendingCandidate).filter(PendingCandidate.url == url).first()


def get_pending_candidate_by_identity(
    db: Session,
    *,
    source_slug: str,
    normalized_artist_name: str,
    normalized_album_title: str,
):
    return (
        db.query(PendingCandidate)
        .filter(
            PendingCandidate.source_slug == source_slug,
            PendingCandidate.normalized_artist_name == normalized_artist_name,
            PendingCandidate.normalized_album_title == normalized_album_title,
        )
        .order_by(PendingCandidate.created_at.desc())
        .first()
    )


def create_pending_candidate(
    db: Session,
    artist_name: str,
    normalized_artist_name: str,
    album_title: str,
    normalized_album_title: str,
    source_slug: str,
    source_product_title: str,
    url: str,
    price: Optional[int] = None,
    cover_image_url: Optional[str] = None,
    note: Optional[str] = None,
):
    candidate = PendingCandidate(
        artist_name=artist_name,
        normalized_artist_name=normalized_artist_name,
        album_title=album_title,
        normalized_album_title=normalized_album_title,
        source_slug=source_slug,
        source_product_title=source_product_title,
        url=url,
        price=price,
        cover_image_url=cover_image_url,
        note=note,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def update_pending_candidate_status(
    db: Session,
    candidate: PendingCandidate,
    status: str,
    matched_release_id: Optional[int] = None,
    note: Optional[str] = None,
):
    candidate.status = status
    candidate.matched_release_id = matched_release_id
    candidate.reviewed_at = datetime.now(timezone.utc)
    if note is not None:
        candidate.note = note
    db.commit()
    db.refresh(candidate)
    return candidate


def refresh_pending_candidate(
    db: Session,
    candidate: PendingCandidate,
    *,
    artist_name: str,
    normalized_artist_name: str,
    album_title: str,
    normalized_album_title: str,
    source_product_title: str,
    url: str,
    price: Optional[int] = None,
    cover_image_url: Optional[str] = None,
):
    candidate.artist_name = artist_name
    candidate.normalized_artist_name = normalized_artist_name
    candidate.album_title = album_title
    candidate.normalized_album_title = normalized_album_title
    candidate.source_product_title = source_product_title
    candidate.url = url
    candidate.price = price
    candidate.cover_image_url = cover_image_url
    db.commit()
    db.refresh(candidate)
    return candidate


def set_pending_candidate_match(
    db: Session,
    candidate: PendingCandidate,
    matched_release_id: Optional[int],
):
    candidate.matched_release_id = matched_release_id
    db.commit()
    db.refresh(candidate)
    return candidate
