import sys
sys.path.insert(0, '.')
from app.database.base import Base
import app.database.models
import app.storage.models
print(sorted(Base.metadata.tables.keys()))
