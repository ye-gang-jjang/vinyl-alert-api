from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.deps import get_db
from schemas.releases import ReleaseIn, ReleaseOut, ReleaseSummaryOut
from services import releases as release_service


router = APIRouter()


@router.get("/releases", response_model=list[ReleaseOut])
def get_releases(db: Session = Depends(get_db)):
    return release_service.get_releases(db)


@router.get("/release-summaries", response_model=list[ReleaseSummaryOut])
def get_release_summaries(db: Session = Depends(get_db)):
    return release_service.get_release_summaries(db)


@router.get("/artists/{artist_name}/release-summaries", response_model=list[ReleaseSummaryOut])
def get_artist_release_summaries(artist_name: str, db: Session = Depends(get_db)):
    return release_service.get_artist_release_summaries(db, artist_name)


@router.get("/releases/{release_id}", response_model=Optional[ReleaseOut])
def get_release_by_id(release_id: str, db: Session = Depends(get_db)):
    return release_service.get_release_by_id(db, release_id)


@router.post("/releases", response_model=ReleaseOut)
def create_release(payload: ReleaseIn, db: Session = Depends(get_db)):
    return release_service.create_release(db, payload)


@router.delete("/releases/{release_id}", status_code=204)
def delete_release(release_id: str, db: Session = Depends(get_db)):
    release_service.delete_release(db, release_id)
