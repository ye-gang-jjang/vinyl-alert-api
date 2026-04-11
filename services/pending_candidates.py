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


def get_pending_candidates(db: Session):
    candidates = pending_repository.list_pending_candidates(db)
    stores = store_repository.list_stores(db)
    store_map = {store.slug: store for store in stores}
    return [_to_pending_candidate_out(candidate, store_map.get(candidate.source_slug)) for candidate in candidates]


def create_pending_candidate(db: Session, payload):
    existing_candidate = pending_repository.get_pending_candidate_by_url(db, payload.url)
    if existing_candidate:
        return _to_pending_candidate_out(
            existing_candidate,
            store_repository.get_store_by_slug(db, existing_candidate.source_slug),
        )

    existing_listing = listing_repository.get_listing_by_store_and_url(db, payload.storeSlug, payload.url)
    if existing_listing:
        raise HTTPException(status_code=409, detail="listing already exists")

    store = store_repository.get_store_by_slug(db, payload.storeSlug)
    if not store:
        raise HTTPException(status_code=400, detail="존재하지 않는 스토어입니다.")

    exact_release = _find_exact_release_match(db, payload.artistName, payload.albumTitle)
    normalized_artist_name = normalize_release_text(payload.artistName)
    normalized_album_title = normalize_release_text(payload.albumTitle)

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


def approve_pending_candidate(db: Session, candidate_id: str, payload):
    try:
        cid = int(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid pending candidate id")

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
