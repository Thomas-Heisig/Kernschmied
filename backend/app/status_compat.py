from __future__ import annotations

from starlette import status as _status

# Provide a single, statically-typed constant that aliases the code
# historically referenced as HTTP_422_UNPROCESSABLE_CONTENT. Some
# environments (and older Starlette versions) use the name
# HTTP_422_UNPROCESSABLE_ENTITY instead. Resolve both at import-time
# so type checkers see a plain `int` symbol and Pylance stops warning.
HTTP_422_UNPROCESSABLE_CONTENT: int = getattr(
    _status,
    "HTTP_422_UNPROCESSABLE_CONTENT",
    getattr(_status, "HTTP_422_UNPROCESSABLE_ENTITY", 422),
)

__all__ = ["HTTP_422_UNPROCESSABLE_CONTENT"]
