from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.normalization import normalize_release_text
from repositories import listings as listing_repository
from repositories import pending_candidates as pending_repository
from repositories import releases as release_repository
from repositories import stores as store_repository
from schemas.pending_candidates import PendingCandidateOut
from schemas.stores import StoreRefOut
from services.serializers import serialize_dt


def _find_exact_release_match(db: Session, artist_name: str, album_title: str):
    normalized_artist_name = normalize_release_text(artist_name)
    normalized_album_title = normalize_release_text(album_title)

    for release in release_repository.list_releases(db):
        if normalize_release_text(release.artist_name) != normalized_artist_name:
            continue
        if normalize_release_text(release.album_title) != normalized_album_title:
            continue
        return release

    return None


def _to_pending_candidate_out(candidate, store):
    store_ref = StoreRefOut(
        slug=candidate.source_slug,
        name=store.name if store else candidate.source_slug,
        iconUrl=store.icon_url if store else "",
    )
    return PendingCandidateOut(
        id=str(candidate.id),
        artistName=candidate.artist_name,
        albumTitle=candidate.album_title,
        sourceProductTitle=candidate.source_product_title,
        url=candidate.url,
        price=candidate.price,
        coverImageUrl=candidate.cover_image_url,
        status=candidate.status,
        note=candidate.note,
        createdAt=serialize_dt(candidate.created_at),
        reviewedAt=serialize_dt(candidate.reviewed_at),
        matchedReleaseId=str(candidate.matched_release_id) if candidate.matched_release_id else None,
        store=store_ref,
    )


def get_pending_candidates(
    db: Session,
    *,
    status: Optional[str] = None,
    store_slug: Optional[str] = None,
    query: Optional[str] = None,
):
    normalized_query = query.strip() if query else None
    candidates = pending_repository.list_pending_candidates(
        db,
        status=status,
        source_slug=store_slug,
        query=normalized_query,
    )
    stores = store_repository.list_stores(db)
    store_map = {store.slug: store for store in stores}
    return [_to_pending_candidate_out(candidate, store_map.get(candidate.source_slug)) for candidate in candidates]


def create_pending_candidate(db: Session, payload):
    normalized_artist_name = normalize_release_text(payload.artistName)
    normalized_album_title = normalize_release_text(payload.albumTitle)

    existing_candidate = pending_repository.get_pending_candidate_by_url(db, payload.url)
    if existing_candidate:
        return _to_pending_candidate_out(
            existing_candidate,
            store_repository.get_store_by_slug(db, existing_candidate.source_slug),
        )

    existing_listing = listing_repository.get_listing_by_store_and_url(db, payload.storeSlug, payload.url)
    if existing_listing:
        raise HTTPException(status_code=409, detail="listing already exists")

    exact_release = _find_exact_release_match(db, payload.artistName, payload.albumTitle)
    if exact_release:
        existing_release_listing = listing_repository.get_listing_by_release_and_store(
            db,
            exact_release.id,
            payload.storeSlug,
        )
        if existing_release_listing:
            raise HTTPException(status_code=409, detail="listing already exists for release and store")

    existing_identity_candidate = pending_repository.get_pending_candidate_by_identity(
        db,
        source_slug=payload.storeSlug,
        normalized_artist_name=normalized_artist_name,
        normalized_album_title=normalized_album_title,
    )
    if existing_identity_candidate:
        refreshed_candidate = pending_repository.refresh_pending_candidate(
            db,
            existing_identity_candidate,
            artist_name=payload.artistName,
            normalized_artist_name=normalized_artist_name,
            album_title=payload.albumTitle,
            normalized_album_title=normalized_album_title,
            source_product_title=payload.sourceProductTitle,
            url=payload.url,
            price=payload.price,
            cover_image_url=payload.coverImageUrl,
        )
        if exact_release and refreshed_candidate.matched_release_id != exact_release.id:
            refreshed_candidate = pending_repository.set_pending_candidate_match(db, refreshed_candidate, exact_release.id)
        if refreshed_candidate is None:
            raise HTTPException(status_code=500, detail="pending candidate refresh failed")
        return _to_pending_candidate_out(
            refreshed_candidate,
            store_repository.get_store_by_slug(db, refreshed_candidate.source_slug),
        )

    store = store_repository.get_store_by_slug(db, payload.storeSlug)
    if not store:
        raise HTTPException(status_code=400, detail="존재하지 않는 스토어입니다.")

    candidate = pending_repository.create_pending_candidate(
        db,
        artist_name=payload.artistName,
        normalized_artist_name=normalized_artist_name,
        album_title=payload.albumTitle,
        normalized_album_title=normalized_album_title,
        source_slug=payload.storeSlug,
        source_product_title=payload.sourceProductTitle,
        url=payload.url,
        price=payload.price,
        cover_image_url=payload.coverImageUrl,
        note=payload.note,
    )

    if exact_release:
        pending_repository.set_pending_candidate_match(db, candidate, exact_release.id)
    return _to_pending_candidate_out(candidate, store)


def _approve_pending_candidate(db: Session, cid: int, payload):
    candidate = pending_repository.get_pending_candidate_by_id(db, cid)
    if not candidate:
        raise HTTPException(status_code=404, detail="pending candidate not found")

    if candidate.status != "PENDING":
        raise HTTPException(status_code=400, detail="candidate already reviewed")

    listing = listing_repository.get_listing_by_store_and_url(db, candidate.source_slug, candidate.url)
    if listing:
        pending_repository.update_pending_candidate_status(
            db,
            candidate,
            status="APPROVED",
            matched_release_id=listing.release_id,
            note="이미 등록된 listing URL과 중복되어 승인 처리됨",
        )
        return _to_pending_candidate_out(candidate, store_repository.get_store_by_slug(db, candidate.source_slug))

    release = None
    release_id = payload.releaseId or (str(candidate.matched_release_id) if candidate.matched_release_id else None)

    if release_id:
        try:
            rid = int(release_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid release id")
        release = release_repository.get_release_by_id(db, rid)
        if not release:
            raise HTTPException(status_code=404, detail="release not found")
    else:
        artist_name = payload.artistName or candidate.artist_name
        album_title = payload.albumTitle or candidate.album_title
        release = release_repository.create_release(
            db,
            artist_name=artist_name,
            album_title=album_title,
            cover_image_url=payload.coverImageUrl or candidate.cover_image_url,
        )

    existing_store_listing = listing_repository.get_listing_by_release_and_store(
        db,
        release.id,
        candidate.source_slug,
    )
    if existing_store_listing:
        pending_repository.update_pending_candidate_status(
            db,
            candidate,
            status="APPROVED",
            matched_release_id=release.id,
            note="이미 같은 앨범/스토어 listing이 존재해 승인 처리됨",
        )
        return _to_pending_candidate_out(candidate, store_repository.get_store_by_slug(db, candidate.source_slug))

    listing_repository.create_listing(
        db,
        release_id=release.id,
        source_slug=candidate.source_slug,
        source_product_title=candidate.source_product_title,
        url=candidate.url,
        price=payload.price if payload.price is not None else candidate.price,
    )

    pending_repository.update_pending_candidate_status(
        db,
        candidate,
        status="APPROVED",
        matched_release_id=release.id,
    )
    return _to_pending_candidate_out(candidate, store_repository.get_store_by_slug(db, candidate.source_slug))


def approve_pending_candidate(db: Session, candidate_id: str, payload):
    try:
        cid = int(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid pending candidate id")

    return _approve_pending_candidate(db, cid, payload)


def reject_pending_candidate(db: Session, candidate_id: str, payload):
    try:
        cid = int(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid pending candidate id")

    candidate = pending_repository.get_pending_candidate_by_id(db, cid)
    if not candidate:
        raise HTTPException(status_code=404, detail="pending candidate not found")

    pending_repository.update_pending_candidate_status(
        db,
        candidate,
        status="REJECTED",
        note=payload.note,
    )
    return _to_pending_candidate_out(candidate, store_repository.get_store_by_slug(db, candidate.source_slug))


def bulk_reject_pending_candidates(db: Session, candidate_ids: List[str], note: Optional[str] = None):
    updated_count = 0

    for candidate_id in candidate_ids:
        try:
            cid = int(candidate_id)
        except ValueError:
            continue

        candidate = pending_repository.get_pending_candidate_by_id(db, cid)
        if not candidate or candidate.status != "PENDING":
            continue

        pending_repository.update_pending_candidate_status(
            db,
            candidate,
            status="REJECTED",
            note=note,
        )
        updated_count += 1

    return {"updatedCount": updated_count}


def bulk_approve_pending_candidates(db: Session, items):
    updated_count = 0

    for item in items:
        try:
            cid = int(item.candidateId)
        except ValueError:
            continue

        try:
            _approve_pending_candidate(db, cid, item)
            updated_count += 1
        except HTTPException as error:
            if error.status_code in {400, 404}:
                continue
            raise

    return {"updatedCount": updated_count}
