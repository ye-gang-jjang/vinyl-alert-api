from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from core.deps import get_db
from schemas.stores import StoreIn, StoreOut, StoreWithCountOut
from services import stores as store_service


router = APIRouter()


@router.get("/stores", response_model=list[StoreWithCountOut])
def get_stores(db: Session = Depends(get_db)):
    return store_service.get_stores(db)


@router.post("/stores", response_model=StoreOut)
def create_store(payload: StoreIn, db: Session = Depends(get_db)):
    return store_service.create_store(db, payload)


@router.delete("/stores/{store_id}", status_code=204)
def delete_store(store_id: str, db: Session = Depends(get_db)):
    store_service.delete_store(db, store_id)
    return Response(status_code=204)
