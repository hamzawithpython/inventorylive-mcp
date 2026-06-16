"""Print the seeded agent API keys from the database."""
import server  # sets up sys.path to backend
from app.core.db import SessionLocal
from app.models import models as m

db = SessionLocal()
try:
    for a in db.query(m.Agent).all():
        print(f"{a.email:24s} role={a.role:6s} api_key={a.api_key}")
finally:
    db.close()