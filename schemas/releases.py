from typing import Optional

from pydantic import BaseModel

from schemas.listings import ListingOut
from schemas.stores import StoreRefOut


class ReleaseIn(BaseModel):
    artistName: str
    albumTitle: str
    coverImageUrl: Optional[str] = None


class ReleaseOut(BaseModel):
    id: str
    artistName: str
    albumTitle: str
    coverImageUrl: Optional[str] = None
    latestCollectedAt: Optional[str] = None
    storesCount: int
    listings: list[ListingOut]
    collectedAt: Optional[str] = None


class ReleaseSummaryOut(BaseModel):
    id: str
    artistName: str
    albumTitle: str
    coverImageUrl: Optional[str] = None
    latestCollectedAt: Optional[str] = None
    storesCount: int
    stores: list[StoreRefOut]
    collectedAt: Optional[str] = None


class PaginatedReleaseSummariesOut(BaseModel):
    items: list[ReleaseSummaryOut]
    page: int
    pageSize: int
    total: int
    totalPages: int
    artists: list[str]
    stores: list[StoreRefOut]
