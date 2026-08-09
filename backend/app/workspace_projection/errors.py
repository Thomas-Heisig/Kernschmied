class ProjectionError(RuntimeError):
    """Generic projection error."""


class PathSanitizationError(ProjectionError):
    """Raised when a supplied name would escape the projection root."""


class AtomicWriteError(ProjectionError):
    """Raised when an atomic file write fails."""


__all__ = ["ProjectionError", "PathSanitizationError", "AtomicWriteError"]
