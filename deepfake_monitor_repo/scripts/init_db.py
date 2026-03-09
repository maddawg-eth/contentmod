import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db import Base, engine
import app.models  # noqa: F401

Base.metadata.create_all(bind=engine)
print("Database tables created")
