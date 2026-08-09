from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Iterable

from .errors import AtomicWriteError


def _atomic_write_json(path: Path, data: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        # atomic replace
        os.replace(str(tmp), str(path))
    except Exception as exc:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        raise AtomicWriteError(str(exc)) from exc


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp), str(path))
    except Exception as exc:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        raise AtomicWriteError(str(exc)) from exc


def write_json(path: Path, obj: Mapping[str, Any]) -> None:
    _atomic_write_json(path, obj)


def write_messages_jsonl(path: Path, messages: Iterable[Mapping[str, Any]]) -> None:
    # write entire file atomically
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as fh:
            for m in messages:
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp), str(path))
    except Exception as exc:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        raise AtomicWriteError(str(exc)) from exc


__all__ = ["write_json", "write_messages_jsonl"]
