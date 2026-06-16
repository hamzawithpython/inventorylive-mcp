"""HTTP-mounted MCP server, sharing the FastAPI process and service layer.

Exposed at /mcp. Auth: the agent api_key is passed as a query/header by the
client; for the hosted demo we resolve it per-call. Reserve fires the live
WebSocket event because this runs in the same process as the hub.
"""
import asyncio
from mcp.server.fastmcp import FastMCP
from app.core.db import SessionLocal
from app.models import models as m
from app.services import inventory as inv_svc
from app.services import reservations as res_svc
from app.services.ws_manager import manager

mcp = FastMCP("InventoryLive")


def _agent_by_key(db, api_key: str):
    agent = db.query(m.Agent).filter(m.Agent.api_key == api_key).first()
    if agent is None:
        raise ValueError("Invalid or missing api_key")
    return agent


@mcp.tool()
def check_availability(api_key: str, max_price_pkr: float | None = None,
                       min_size_marla: float | None = None) -> list[dict]:
    """List available units in the api_key holder''s permitted scope."""
    db = SessionLocal()
    try:
        agent = _agent_by_key(db, api_key)
        units = inv_svc.list_units(db, agent, status="available")
        out = []
        for u in units:
            if max_price_pkr is not None and float(u.price_pkr) > max_price_pkr:
                continue
            if min_size_marla is not None and float(u.size_marla) < min_size_marla:
                continue
            block = db.query(m.Block).filter(m.Block.id == u.block_id).first()
            proj = db.query(m.Project).filter(m.Project.id == block.project_id).first()
            out.append({
                "unit_id": u.id, "unit_number": u.unit_number, "project": proj.name,
                "block": block.name, "size_marla": float(u.size_marla),
                "floor": u.floor, "price_pkr": float(u.price_pkr),
            })
        return out
    finally:
        db.close()


@mcp.tool()
def inventory_summary(api_key: str, project: str) -> dict:
    """Counts of available/reserved/sold for a project within scope."""
    db = SessionLocal()
    try:
        agent = _agent_by_key(db, api_key)
        proj = db.query(m.Project).filter(m.Project.name.ilike(f"%{project}%")).first()
        if proj is None:
            return {"error": f"No project matching ''{project}''"}
        counts = inv_svc.inventory_summary(db, agent, proj.id)
        return {"project": proj.name, **counts}
    finally:
        db.close()


@mcp.tool()
def reserve_unit(api_key: str, unit_id: int) -> dict:
    """Reserve a unit as the api_key holder. Fires the live portal update."""
    db = SessionLocal()
    try:
        agent = _agent_by_key(db, api_key)
        result = res_svc.reserve_unit(db, agent, unit_id, source="mcp")
        # Same-process: push the live WebSocket event so the portal updates instantly.
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(manager.broadcast_unit_change(result["block_id"], {
                "type": "unit_changed", "unit_id": result["unit_id"],
                "status": result["status"], "version": result["version"],
                "by": result["reserved_by"], "source": "mcp",
            }))
        except RuntimeError:
            pass  # no running loop in some contexts; DB state is still correct
        return result
    except res_svc.ReservationError as e:
        return {"error": str(e)}
    finally:
        db.close()