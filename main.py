# =========================
# Imports
# =========================
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import health, listings, pending_candidates, releases, stores


# =========================
# App
# =========================
app = FastAPI(title="Vinyl Alert API")


# =========================
# Middleware (CORS)
# =========================
def get_allowed_origins():
    raw = os.getenv("ALLOW_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


ALLOWED_ORIGINS = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(releases.router)
app.include_router(listings.router)
app.include_router(stores.router)
app.include_router(pending_candidates.router)
