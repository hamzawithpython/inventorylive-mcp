"""InventoryLive MCP server.

Exposes the SAME live inventory as the portal, enforcing the SAME RBAC,
reusing the SAME service layer. The agent is identified by an api_key passed
via the INVENTORYLIVE_API_KEY environment variable (set in the MCP client
config). Every tool resolves that key to an agent and scopes results to that
agent''s permitted blocks.

Transport: stdio (the client launches this as a subprocess).
"""
import os
import sys
from pathlib import Path

# Make the backend package importable (shared service layer, no duplication).
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from mcp.server.fastmcp import FastMCP  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.models import models as m  # noqa: E402
from app.services import inventory as inv_svc  # noqa: E402
from app.services import reservations as res_svc  # noqa: E402

mcp = FastMCP("InventoryLive")


def _current_agent(db):
    """Resolve the api_key from env to an Agent, or raise."""
    api_key = os.environ.get("INVENTORYLIVE_API_KEY", "")
    agent = db.query(m.Agent).filter(m.Agent.api_key == api_key).first()
    if agent is None:
        raise ValueError("Invalid or missing INVENTORYLIVE_API_KEY")
    return agent


@mcp.tool()
def check_availability(project: str | None = None,
                       max_price_pkr: float | None = None,
                       min_size_marla: float | None = None) -> list[dict]:
    """List available units the current agent may access.

    Optionally filter by project name, max price (PKR), and minimum size (marla).
    Returns only AVAILABLE units within the agent''s permitted scope.
    """
    db = SessionLocal()
    try:
        agent = _current_agent(db)
        units = inv_svc.list_units(db, agent, status="available")
        out = []
        for u in units:
            if max_price_pkr is not None and float(u.price_pkr) > max_price_pkr:
                continue
            if min_size_marla is not None and float(u.size_marla) < min_size_marla:
                continue
            block = db.query(m.Block).filter(m.Block.id == u.block_id).first()
            proj = db.query(m.Project).filter(m.Project.id == block.project_id).first()
            if project is not None and project.lower() not in proj.name.lower():
                continue
            out.append({
                "unit_id": u.id,
                "unit_number": u.unit_number,
                "project": proj.name,
                "block": block.name,
                "size_marla": float(u.size_marla),
                "floor": u.floor,
                "price_pkr": float(u.price_pkr),
            })
        return out
    finally:
        db.close()


@mcp.tool()
def get_unit_details(unit_id: int) -> dict:
    """Get full details for one unit, if the current agent may access it."""
    db = SessionLocal()
    try:
        agent = _current_agent(db)
        # Reuse the scoped query: list within scope, then pick.
        units = inv_svc.list_units(db, agent)
        match = next((u for u in units if u.id == unit_id), None)
        if match is None:
            return {"error": "Unit not found or not permitted"}
        block = db.query(m.Block).filter(m.Block.id == match.block_id).first()
        proj = db.query(m.Project).filter(m.Project.id == block.project_id).first()
        return {
            "unit_id": match.id,
            "unit_number": match.unit_number,
            "project": proj.name,
            "block": block.name,
            "size_marla": float(match.size_marla),
            "floor": match.floor,
            "price_pkr": float(match.price_pkr),
            "status": match.status,
        }
    finally:
        db.close()


@mcp.tool()
def inventory_summary(project: str) -> dict:
    """Counts of available/reserved/sold for a project, within agent scope.

    Matches the project by (partial) name.
    """
    db = SessionLocal()
    try:
        agent = _current_agent(db)
        proj = (
            db.query(m.Project)
            .filter(m.Project.name.ilike(f"%{project}%"))
            .first()
        )
        if proj is None:
            return {"error": f"No project matching ''{project}''"}
        counts = inv_svc.inventory_summary(db, agent, proj.id)
        return {"project": proj.name, **counts}
    finally:
        db.close()


@mcp.tool()
def reserve_unit(unit_id: int) -> dict:
    """Place a time-limited hold on a unit as the current agent.

    Uses the SAME row-locked reservation logic as the portal. Reserving here
    is recorded with source=''mcp'' in the audit log. NOTE: this does not push
    the live WebSocket event (that runs in the API process); the hold itself
    is fully applied in the shared database and visible on the portal''s next
    fetch. Real-time push from MCP is wired in the HTTP/SSE variant.
    """
    db = SessionLocal()
    try:
        agent = _current_agent(db)
        result = res_svc.reserve_unit(db, agent, unit_id, source="mcp")
        return result
    except res_svc.ReservationError as e:
        return {"error": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()