from sqlalchemy.orm import Session

from models import Store


def list_stores(db: Session):
    return db.query(Store).order_by(Store.name.asc()).all()


def get_store_by_slug(db: Session, slug: str):
    return db.query(Store).filter(Store.slug == slug).first()


def get_store_by_id(db: Session, store_id: int):
    return db.query(Store).filter(Store.id == store_id).first()


def get_stores_by_slugs(db: Session, slugs: list[str]):
    if not slugs:
        return []
    return db.query(Store).filter(Store.slug.in_(slugs)).all()


def create_store(db: Session, name: str, slug: str, icon_url: str):
    store = Store(name=name, slug=slug, icon_url=icon_url)
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def delete_store(db: Session, store: Store):
    db.delete(store)
    db.commit()
