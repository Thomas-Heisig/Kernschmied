import sys
sys.path.insert(0, '.')
from app.database.base import Base
import importlib

# ensure model modules are imported so they register with SQLAlchemy metadata
importlib.import_module("app.database.models")
importlib.import_module("app.storage.models")

print(sorted(Base.metadata.tables.keys()))
