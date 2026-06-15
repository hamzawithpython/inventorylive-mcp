"""InventoryLive API entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inventory

app = FastAPI(title="InventoryLive API")

# CORS open for local dev; tighten before deploy (Phase 6)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory.router)


@app.get("/health")
def health():
    return {"status": "ok"}