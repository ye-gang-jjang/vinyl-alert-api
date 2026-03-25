from pydantic import BaseModel


class StoreIn(BaseModel):
    name: str
    slug: str
    iconUrl: str


class StoreOut(BaseModel):
    id: str
    name: str
    slug: str
    iconUrl: str


class StoreWithCountOut(StoreOut):
    listingsCount: int


class StoreRefOut(BaseModel):
    slug: str
    name: str
    iconUrl: str
