import sys

sys.path.insert(0, '.')
from app.storage.models.chat import Chat
from app.storage.models.hierarchy import HierarchyNode

n = HierarchyNode(node_type='conversation_root', name='root', prompt=None, position=0, config={}, is_active=True)
print('Created node:', n)
print('Attributes:', n.type, n.node_metadata if hasattr(n, 'node_metadata') else None)
# Check Chat FK column
print('Chat.node_id column foreign keys:', list(Chat.__table__.c.node_id.foreign_keys))
