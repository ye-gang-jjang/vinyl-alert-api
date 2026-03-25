from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.deps import get_db
from schemas.listings import ListingIn, ListingOut, ListingUpdate
from schemas.releases import ReleaseOut
from services import listings as listing_service


router = APIRouter()


@router.post("/releases/{release_id}/listings", response_model=Optional[ReleaseOut])
def add_listing(release_id: str, payload: ListingIn, db: Session = Depends(get_db)):
    return listing_service.add_listing(db, release_id, payload)


@router.patch("/listings/{listing_id}", response_model=ListingOut)
def update_listing(listing_id: str, payload: ListingUpdate, db: Session = Depends(get_db)):
    return listing_service.update_listing(db, listing_id, payload)


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(listing_id: str, db: Session = Depends(get_db)):
    listing_service.delete_listing(db, listing_id)
