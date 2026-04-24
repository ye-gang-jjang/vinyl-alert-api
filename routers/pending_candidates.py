from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.deps import get_db
from schemas.pending_candidates import (
    ApprovePendingCandidateIn,
    BulkApprovePendingCandidatesIn,
    BulkRejectPendingCandidatesIn,
    PendingCandidateBulkActionOut,
    PendingCandidateIn,
    PendingCandidateOut,
    RejectPendingCandidateIn,
)
from services import pending_candidates as pending_service


router = APIRouter()


@router.get("/pending-candidates", response_model=list[PendingCandidateOut])
def get_pending_candidates(
    status: Optional[str] = Query(default=None),
    storeSlug: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return pending_service.get_pending_candidates(db, status=status, store_slug=storeSlug, query=q)


@router.post("/pending-candidates", response_model=PendingCandidateOut)
def create_pending_candidate(payload: PendingCandidateIn, db: Session = Depends(get_db)):
    return pending_service.create_pending_candidate(db, payload)


@router.post("/pending-candidates/bulk/reject", response_model=PendingCandidateBulkActionOut)
def bulk_reject_pending_candidates(
    payload: BulkRejectPendingCandidatesIn,
    db: Session = Depends(get_db),
):
    return pending_service.bulk_reject_pending_candidates(db, payload.candidateIds, payload.note)


@router.post("/pending-candidates/bulk/approve", response_model=PendingCandidateBulkActionOut)
def bulk_approve_pending_candidates(
    payload: BulkApprovePendingCandidatesIn,
    db: Session = Depends(get_db),
):
    return pending_service.bulk_approve_pending_candidates(db, payload.items)


@router.post("/pending-candidates/{candidate_id}/approve", response_model=PendingCandidateOut)
def approve_pending_candidate(
    candidate_id: str,
    payload: ApprovePendingCandidateIn,
    db: Session = Depends(get_db),
):
    return pending_service.approve_pending_candidate(db, candidate_id, payload)


@router.post("/pending-candidates/{candidate_id}/reject", response_model=PendingCandidateOut)
def reject_pending_candidate(
    candidate_id: str,
    payload: RejectPendingCandidateIn,
    db: Session = Depends(get_db),
):
    return pending_service.reject_pending_candidate(db, candidate_id, payload)
