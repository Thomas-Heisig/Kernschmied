from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path


def safe_storage_path(root: Path, *, node_id: str, file_id: str) -> Path:
    """Deterministically compute a storage path under root for a file.

    The path layout is: <root>/nodes/<node_id[:2]>/<node_id>/<file_id>
    This avoids client-controlled paths and keeps files namespaced by node.
    """
    # ensure no absolute or parent-traversal components are used
    # file_id and node_id are expected to be simple UUID strings
    nseg = node_id[:2]
    return root.joinpath("nodes", nseg, node_id, file_id)


def atomic_write_bytes(
    target: Path,
    data_stream,
    *,
    tmp_dir: Path | None = None,
) -> tuple[Path, int]:
    """Write bytes from an async-compatible stream to a temp file, fsync,
    then atomically replace target.

    Returns (final_path, size).
    """
    tmp_dir = tmp_dir or target.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(dir=str(tmp_dir))
    tmp_path = Path(tmp_path_str)
    try:
        # write in binary chunks
        total = 0
        with os.fdopen(fd, "wb") as f:
            for chunk in data_stream:
                if not chunk:
                    continue
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")
                f.write(chunk)
                total += len(chunk)
            f.flush()
            os.fsync(f.fileno())

        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(tmp_path), str(target))
        return target, total
    finally:
        if tmp_path.exists():
            with contextlib.suppress(Exception):
                tmp_path.unlink()
