"""RBAC chokepoint. Resolves an agent to the block IDs they may access.

EVERY read/write path — REST, WebSocket fan-out, MCP tools — calls
get_permitted_block_ids() so the same rule is enforced everywhere.
"""
from sqlalchemy.orm import Session
from app.models import models as m

# Sentinel: admins may access everything.
ALL_BLOCKS = "ALL"


def get_permitted_block_ids(db: Session, agent: m.Agent):
    """Return set of block_ids this agent may access, or ALL_BLOCKS for admins."""
    if agent.role == "admin":
        return ALL_BLOCKS

    permitted: set[int] = set()
    perms = db.query(m.Permission).filter(m.Permission.agent_id == agent.id).all()
    for p in perms:
        if p.block_id is not None:
            # Scoped to a single block.
            permitted.add(p.block_id)
        else:
            # Whole-project grant: add every block in that project.
            blocks = db.query(m.Block).filter(m.Block.project_id == p.project_id).all()
            permitted.update(b.id for b in blocks)
    return permitted


def is_block_allowed(permitted, block_id: int) -> bool:
    """Uniform check used by all access paths."""
    return permitted == ALL_BLOCKS or block_id in permitted