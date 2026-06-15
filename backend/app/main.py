"""InventoryLive API entrypoint with background hold-expiry sweeper."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inventory, auth, reservations, ws
from app.core.db import SessionLocal
from app.core.config import settings
from app.services.reservations import release_expired
from app.services.ws_manager import manager

SWEEP_INTERVAL_SECONDS = 30


async def hold_sweeper():
    while True:
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            freed = release_expired(db)
            for unit_id, block_id, version in freed:
                await manager.broadcast_unit_change(block_id, {
                    "type": "unit_changed",
                    "unit_id": unit_id,
                    "status": "available",
                    "version": version,
                    "by": None,
                    "source": "system",
                })
            if freed:
                print(f"[sweeper] released + broadcast: {[u for u,_,_ in freed]}")
        except Exception as e:  # noqa: BLE001
            print(f"[sweeper] error: {e}")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(hold_sweeper())
    yield
    task.cancel()


app = FastAPI(title="InventoryLive API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(reservations.router)
app.include_router(ws.router)


@app.get("/")
def root():
    return {"service": "InventoryLive API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok"}