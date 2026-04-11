from typing import Optional

from pydantic import BaseModel

from schemas.stores import StoreRefOut


class PendingCandidateIn(BaseModel):
    artistName: str
    albumTitle: str
    storeSlug: str
    sourceProductTitle: str
    url: str
    price: Optional[int] = None
    coverImageUrl: Optional[str] = None
    note: Optional[str] = None


class ApprovePendingCandidateIn(BaseModel):
    releaseId: Optional[str] = None
    artistName: Optional[str] = None
    albumTitle: Optional[str] = None
    coverImageUrl: Optional[str] = None
    price: Optional[int] = None


class RejectPendingCandidateIn(BaseModel):
    note: Optional[str] = None


class PendingCandidateOut(BaseModel):
    id: str
    artistName: str
    albumTitle: str
    sourceProductTitle: str
    url: str
    price: Optional[int] = None
    coverImageUrl: Optional[str] = None
    status: str
    note: Optional[str] = None
    createdAt: Optional[str] = None
    reviewedAt: Optional[str] = None
    matchedReleaseId: Optional[str] = None
    store: StoreRefOut
