from typing import Optional

from sqlalchemy.orm import Session

from models import Listing


def get_listing_by_id(db: Session, listing_id: int):
    return db.query(Listing).filter(Listing.id == listing_id).first()


def get_listing_by_store_and_url(db: Session, source_slug: str, url: str):
    return (
        db.query(Listing)
        .filter(Listing.source_slug == source_slug, Listing.url == url)
        .first()
    )


def get_listing_by_release_and_store(db: Session, release_id: int, source_slug: str):
    return (
        db.query(Listing)
        .filter(Listing.release_id == release_id, Listing.source_slug == source_slug)
        .first()
    )


def create_listing(
    db: Session,
    release_id: int,
    source_slug: str,
    source_product_title: str,
    url: str,
    price: Optional[int],
):
    listing = Listing(
        release_id=release_id,
        source_slug=source_slug,
        source_product_title=source_product_title,
        url=url,
        price=price,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def delete_listing(db: Session, listing: Listing):
    db.delete(listing)
    db.commit()


def count_listings_by_store_slug(db: Session, store_slug: str):
    return db.query(Listing).filter(Listing.source_slug == store_slug).count()
