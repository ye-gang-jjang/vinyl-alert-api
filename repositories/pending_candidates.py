from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models import PendingCandidate


def list_pending_candidates(db: Session):
    return (
        db.query(PendingCandidate)
        .order_by(PendingCandidate.status.asc(), PendingCandidate.created_at.desc())
        .all()
    )


def get_pending_candidate_by_id(db: Session, candidate_id: int):
    return db.query(PendingCandidate).filter(PendingCandidate.id == candidate_id).first()


def get_pending_candidate_by_url(db: Session, url: str):
    return db.query(PendingCandidate).filter(PendingCandidate.url == url).first()


def create_pending_candidate(
    db: Session,
    artist_name: str,
    normalized_artist_name: str,
    album_title: str,
    normalized_album_title: str,
    source_slug: str,
    source_product_title: str,
    url: str,
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


def set_pending_candidate_match(
    db: Session,
    candidate: PendingCandidate,
    matched_release_id: Optional[int],
):
    candidate.matched_release_id = matched_release_id
    db.commit()
    db.refresh(candidate)
    return candidate
