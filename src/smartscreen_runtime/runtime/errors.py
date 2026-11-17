class RuntimeError(Exception):
    """Base runtime error."""


class InvalidRuntimeStateError(RuntimeError):
    """Raised when a lifecycle transition is invalid."""
