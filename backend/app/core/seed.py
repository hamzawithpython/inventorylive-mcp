"""Idempotent synthetic Pakistani housing-society data.

Wipes and reseeds. NO real developer data Ã¢â‚¬â€ all generated.
"""
import secrets
import random
from app.core.db import SessionLocal, engine, Base
from app.models import models as m
from app.core.security import hash_password

PROJECTS = [
    ("Bahria Town Phase 8", "Rawalpindi"),
    ("DHA Valley", "Islamabad"),
]
BLOCKS_PER_PROJECT = ["Block A", "Block B", "Block C", "Block D"]
SIZES = [5.0, 10.0, 20.0]  # marla; 20 marla = 1 kanal
PRICE_PER_MARLA = {5.0: 4_500_000, 10.0: 4_000_000, 20.0: 3_500_000}
STATUS_WEIGHTS = (["available"] * 7) + (["reserved"] * 2) + (["sold"] * 1)


def wipe():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        for pname, city in PROJECTS:
            proj = m.Project(name=pname, city=city)
            db.add(proj)
            db.flush()
            for bname in BLOCKS_PER_PROJECT:
                block = m.Block(project_id=proj.id, name=bname)
                db.add(block)
                db.flush()
                for i in range(1, random.randint(30, 50)):
                    size = random.choice(SIZES)
                    base = PRICE_PER_MARLA[size] * size
                    price = base * random.uniform(0.9, 1.25)
                    unit = m.Unit(
                        block_id=block.id,
                        unit_number=f"{bname[-1]}-{i:03d}",
                        size_marla=size,
                        floor=random.randint(0, 3),
                        price_pkr=round(price, 2),
                        status=random.choice(STATUS_WEIGHTS),
                        version=0,
                    )
                    db.add(unit)
        db.flush()

        projects = db.query(m.Project).all()
        blocks = db.query(m.Block).all()

        admin = m.Agent(
            email="admin@demo.com",
            hashed_password=hash_password("demo1234"),
            role="admin",
            api_key="admin_" + secrets.token_hex(16),
        )
        agent_a = m.Agent(
            email="agent_a@demo.com", hashed_password=hash_password("demo1234"),
            role="agent", api_key="agentA_" + secrets.token_hex(16),
        )
        agent_b = m.Agent(
            email="agent_b@demo.com", hashed_password=hash_password("demo1234"),
            role="agent", api_key="agentB_" + secrets.token_hex(16),
        )
        db.add_all([admin, agent_a, agent_b])
        db.flush()

        db.add(m.Permission(agent_id=agent_a.id, project_id=projects[0].id, block_id=None))
        first_block = [b for b in blocks if b.project_id == projects[0].id][0]
        db.add(m.Permission(
            agent_id=agent_b.id, project_id=projects[0].id, block_id=first_block.id
        ))

        db.commit()

        print("Seed complete.")
        print(f"  admin   api_key: {admin.api_key}")
        print(f"  agent_a api_key: {agent_a.api_key}  (scope: {projects[0].name})")
        print(f"  agent_b api_key: {agent_b.api_key}  (scope: {projects[0].name} / {first_block.name})")
        units = db.query(m.Unit).count()
        print(f"  units seeded: {units}")
    finally:
        db.close()


if __name__ == "__main__":
    wipe()
    seed()