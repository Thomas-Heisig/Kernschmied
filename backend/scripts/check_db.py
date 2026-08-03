import sqlite3
from pathlib import Path

# Adjust DB path based on settings above
db = Path(r'F:\Kernschmied\backend\data\chat.db')
connection = sqlite3.connect(db)
cursor = connection.cursor()

print('Alembic:')
try:
    print(cursor.execute('SELECT version_num FROM alembic_version').fetchall())
except Exception as e:
    print('alembic_version not found or error:', e)

print('\nSystem-Root:')
try:
    print(cursor.execute(
        '''
        SELECT
            id,
            parent_id,
            type,
            name,
            is_system,
            is_movable,
            is_deletable,
            prompt_enabled,
            prompt_priority,
            prompt_mode
        FROM hierarchy_nodes
        WHERE id = 'system-root'
        '''
    ).fetchall())
except Exception as e:
    print('query error:', e)

print('\nKnoten ohne Parent:')
try:
    print(cursor.execute(
        '''
        SELECT id, type, name
        FROM hierarchy_nodes
        WHERE parent_id IS NULL
        ORDER BY position, id
        '''
    ).fetchall())
except Exception as e:
    print('query error:', e)

print('\nHierarchie:')
try:
    print(cursor.execute(
        '''
        SELECT id, parent_id, type, name, position
        FROM hierarchy_nodes
        ORDER BY parent_id, position, id
        '''
    ).fetchall())
except Exception as e:
    print('query error:', e)

print('\nForeign-Key-Pruefung:')
try:
    print(cursor.execute('PRAGMA foreign_key_check').fetchall())
except Exception as e:
    print('pragma error:', e)

print('\nIntegritaet:')
try:
    print(cursor.execute('PRAGMA integrity_check').fetchall())
except Exception as e:
    print('pragma error:', e)

connection.close()
