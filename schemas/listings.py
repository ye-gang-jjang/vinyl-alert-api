from typing import Optional

from pydantic import BaseModel


class ListingIn(BaseModel):
    storeSlug: str
    sourceProductTitle: str
    url: str
    price: Optional[int] = None


class ListingUpdate(BaseModel):
    storeSlug: Optional[str] = None
    sourceProductTitle: Optional[str] = None
    price: Optional[int] = None


class ListingOut(BaseModel):
    id: str
    sourceName: str
    sourceProductTitle: str
    url: str
    collectedAt: Optional[str] = None
    imageUrl: str
    latestCollectedAt: Optional[str] = None
    price: Optional[int] = None
