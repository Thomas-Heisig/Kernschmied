"""Application package initialisation.

Monkey-patch SQLAlchemy's `create_async_engine` to default to
`NullPool` for SQLite URLs. Many tests create temporary on-disk
SQLite databases via `create_async_engine(...)` and forget to dispose
them explicitly; forcing `NullPool` reduces lingering file handles on
Windows and prevents PermissionError warnings during tempfile cleanup.
"""
from sqlalchemy.ext.asyncio import create_async_engine as _orig_create_async_engine
from sqlalchemy.pool import NullPool


def create_async_engine(url: str | object, **kwargs):
	"""Wrapper around SQLAlchemy's create_async_engine.

	If the URL indicates SQLite and no explicit `poolclass` is given,
	set `NullPool` to avoid file handles being held across GC cycles.
	"""
	try:
		u = str(url)
	except Exception:
		u = ""

	if u.startswith("sqlite") and "poolclass" not in kwargs:
		kwargs = dict(kwargs)
		kwargs.setdefault("poolclass", NullPool)

	return _orig_create_async_engine(url, **kwargs)


# Export the wrapped function so callers using `from sqlalchemy.ext.asyncio import create_async_engine`
# will still get the original when importing directly from SQLAlchemy; however,
# importing via `app` package and referencing `app.create_async_engine` will use
# the wrapped version. Tests import `app.*` before creating engines, so this
# reduces the common tempfile locking warnings on Windows.
__all__ = ["create_async_engine"]
