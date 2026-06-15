"""InventoryLive API entrypoint with background hold-expiry sweeper."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inventory, auth, reservations
from app.core.db import SessionLocal
from app.services.reservations import release_expired

SWEEP_INTERVAL_SECONDS = 30


async def hold_sweeper():
    """Periodically release expired holds back to available."""
    while True:
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            freed = release_expired(db)
            if freed:
                print(f"[sweeper] released expired holds: {freed}")
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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(reservations.router)


@app.get("/health")
def health():
    return {"status": "ok"}