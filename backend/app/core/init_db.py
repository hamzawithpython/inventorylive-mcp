"""Create all tables. Run once before seeding."""
from app.core.db import Base, engine
from app.models import models  # noqa: F401  (registers models on Base)


def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    main()