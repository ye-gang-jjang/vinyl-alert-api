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

    for release in release_repository.list_releases_for_matching(db):
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
        createdAt=serialize_dt(candidate.created_at),
        reviewedAt=serialize_dt(candidate.reviewed_at),
        matchedReleaseId=str(candidate.matched_release_id) if candidate.matched_release_id else None,
        store=store_ref,
    )


def _build_store_map(db: Session, source_slugs: list[str]):
    stores = store_repository.get_stores_by_slugs(db, sorted(set(source_slugs)))
    return {store.slug: store for store in stores}


def _get_candidate_store_map(db: Session, candidates):
    source_slugs = [candidate.source_slug for candidate in candidates if candidate and candidate.source_slug]
    return _build_store_map(db, source_slugs)


def _approve_pending_candidate_record(db: Session, candidate, payload, store, *, commit: bool = True):
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
            commit=commit,
        )
        return _to_pending_candidate_out(candidate, store)

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
            commit=False,
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
            commit=commit,
        )
        return _to_pending_candidate_out(candidate, store)

    listing_repository.create_listing(
        db,
        release_id=release.id,
        source_slug=candidate.source_slug,
        source_product_title=candidate.source_product_title,
        url=candidate.url,
        price=payload.price if payload.price is not None else candidate.price,
        commit=False,
    )

    pending_repository.update_pending_candidate_status(
        db,
        candidate,
        status="APPROVED",
        matched_release_id=release.id,
        commit=False,
    )

    if commit:
        db.commit()
        db.refresh(candidate)

    return _to_pending_candidate_out(candidate, store)


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
    store_map = _get_candidate_store_map(db, candidates)
    return [_to_pending_candidate_out(candidate, store_map.get(candidate.source_slug)) for candidate in candidates]


def create_pending_candidate(db: Session, payload):
    normalized_artist_name = normalize_release_text(payload.artistName)
    normalized_album_title = normalize_release_text(payload.albumTitle)
    store = store_repository.get_store_by_slug(db, payload.storeSlug)
    if not store:
        raise HTTPException(status_code=400, detail="존재하지 않는 스토어입니다.")

    existing_candidate = pending_repository.get_pending_candidate_by_url(db, payload.url)
    if existing_candidate:
        existing_store = store if existing_candidate.source_slug == store.slug else None
        if existing_store is None:
            existing_store_map = _build_store_map(db, [existing_candidate.source_slug])
            existing_store = existing_store_map.get(existing_candidate.source_slug)
        return _to_pending_candidate_out(existing_candidate, existing_store)

    existing_listing = listing_repository.get_listing_by_store_and_url(db, payload.storeSlug, payload.url)
    if existing_listing:
        raise HTTPException(status_code=409, detail="listing already exists")

    existing_identity_candidate = pending_repository.get_pending_candidate_by_identity(
        db,
        source_slug=payload.storeSlug,
        normalized_artist_name=normalized_artist_name,
        normalized_album_title=normalized_album_title,
    )
    if existing_identity_candidate:
        try:
            exact_release = None
            if existing_identity_candidate.matched_release_id is None:
                exact_release = _find_exact_release_match(db, payload.artistName, payload.albumTitle)
                if exact_release:
                    existing_release_listing = listing_repository.get_listing_by_release_and_store(
                        db,
                        exact_release.id,
                        payload.storeSlug,
                    )
                    if existing_release_listing:
                        raise HTTPException(status_code=409, detail="listing already exists for release and store")

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
                commit=False,
            )
            if exact_release and refreshed_candidate.matched_release_id != exact_release.id:
                refreshed_candidate = pending_repository.set_pending_candidate_match(
                    db,
                    refreshed_candidate,
                    exact_release.id,
                    commit=False,
                )
            db.commit()
            db.refresh(refreshed_candidate)
            return _to_pending_candidate_out(refreshed_candidate, store)
        except Exception:
            db.rollback()
            raise

    try:
        exact_release = _find_exact_release_match(db, payload.artistName, payload.albumTitle)
        if exact_release:
            existing_release_listing = listing_repository.get_listing_by_release_and_store(
                db,
                exact_release.id,
                payload.storeSlug,
            )
            if existing_release_listing:
                raise HTTPException(status_code=409, detail="listing already exists for release and store")

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
            commit=False,
        )

        if exact_release:
            pending_repository.set_pending_candidate_match(
                db,
                candidate,
                exact_release.id,
                commit=False,
            )
        db.commit()
        db.refresh(candidate)
        return _to_pending_candidate_out(candidate, store)
    except Exception:
        db.rollback()
        raise


def _approve_pending_candidate(db: Session, cid: int, payload, *, commit: bool = True):
    candidate = pending_repository.get_pending_candidate_by_id(db, cid)
    if not candidate:
        raise HTTPException(status_code=404, detail="pending candidate not found")
    store_map = _get_candidate_store_map(db, [candidate])
    store = store_map.get(candidate.source_slug)
    return _approve_pending_candidate_record(db, candidate, payload, store, commit=commit)


def approve_pending_candidate(db: Session, candidate_id: str, payload):
    try:
        cid = int(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid pending candidate id")

    try:
        return _approve_pending_candidate(db, cid, payload)
    except Exception:
        db.rollback()
        raise


def reject_pending_candidate(db: Session, candidate_id: str, payload):
    try:
        cid = int(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid pending candidate id")

    candidate = pending_repository.get_pending_candidate_by_id(db, cid)
    if not candidate:
        raise HTTPException(status_code=404, detail="pending candidate not found")

    store_map = _get_candidate_store_map(db, [candidate])
    store = store_map.get(candidate.source_slug)

    try:
        pending_repository.update_pending_candidate_status(
            db,
            candidate,
            status="REJECTED",
        )
        return _to_pending_candidate_out(candidate, store)
    except Exception:
        db.rollback()
        raise


def bulk_reject_pending_candidates(db: Session, candidate_ids: List[str]):
    updated_count = 0
    parsed_ids = []

    for candidate_id in candidate_ids:
        try:
            parsed_ids.append(int(candidate_id))
        except ValueError:
            continue

    candidates = pending_repository.get_pending_candidates_by_ids(db, parsed_ids)
    candidate_map = {candidate.id: candidate for candidate in candidates}

    try:
        for cid in parsed_ids:
            candidate = candidate_map.get(cid)
            if not candidate or candidate.status != "PENDING":
                continue

            pending_repository.update_pending_candidate_status(
                db,
                candidate,
                status="REJECTED",
                commit=False,
            )
            updated_count += 1

        db.commit()
        return {"updatedCount": updated_count}
    except Exception:
        db.rollback()
        raise


def bulk_approve_pending_candidates(db: Session, items):
    updated_count = 0
    candidate_ids = []

    for item in items:
        try:
            candidate_ids.append(int(item.candidateId))
        except ValueError:
            continue

    candidates = pending_repository.get_pending_candidates_by_ids(db, candidate_ids)
    candidate_map = {candidate.id: candidate for candidate in candidates}
    store_map = _get_candidate_store_map(db, candidates)

    for item in items:
        try:
            cid = int(item.candidateId)
        except ValueError:
            continue

        try:
            candidate = candidate_map.get(cid)
            store = store_map.get(candidate.source_slug) if candidate else None
            _approve_pending_candidate_record(db, candidate, item, store, commit=False)
            db.commit()
            updated_count += 1
        except HTTPException as error:
            db.rollback()
            if error.status_code in {400, 404}:
                continue
            raise
        except Exception:
            db.rollback()
            raise

    return {"updatedCount": updated_count}


def reopen_pending_candidate(db: Session, candidate_id: str):
    try:
        cid = int(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid pending candidate id")

    candidate = pending_repository.get_pending_candidate_by_id(db, cid)
    if not candidate:
        raise HTTPException(status_code=404, detail="pending candidate not found")

    if candidate.status != "REJECTED":
        raise HTTPException(status_code=400, detail="candidate is not rejected")

    store_map = _get_candidate_store_map(db, [candidate])
    store = store_map.get(candidate.source_slug)

    try:
        reopened_candidate = pending_repository.reopen_pending_candidate(db, candidate)
        return _to_pending_candidate_out(reopened_candidate, store)
    except Exception:
        db.rollback()
        raise
