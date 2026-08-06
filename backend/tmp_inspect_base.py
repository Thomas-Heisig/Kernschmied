import sys

sys.path.insert(0, '.')
from app.database.base import Base

print('Base:', Base)
print('hasattr(Base, "metadata")', hasattr(Base, 'metadata'))
print('type(Base.metadata):', type(Base.metadata))
print('repr(Base.metadata):', repr(Base.metadata))
