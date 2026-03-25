from typing import Literal, Optional

from pydantic import BaseModel


ListingStatus = Literal["ON_SALE", "PREORDER", "SOLD_OUT"]


class ListingIn(BaseModel):
    storeSlug: str
    sourceProductTitle: str
    url: str
    price: Optional[int] = None
    status: ListingStatus = "ON_SALE"


class ListingUpdate(BaseModel):
    price: Optional[int] = None
    status: Optional[ListingStatus] = None


class ListingOut(BaseModel):
    id: str
    sourceName: str
    sourceProductTitle: str
    url: str
    collectedAt: Optional[str] = None
    imageUrl: str
    latestCollectedAt: Optional[str] = None
    price: Optional[int] = None
    status: str
