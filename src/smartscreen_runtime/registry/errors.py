class CapabilityRegistryError(Exception):
    """Base error for capability registry operations."""


class CapabilityAlreadyRegisteredError(CapabilityRegistryError):
    """Raised when a capability identifier is already registered."""


class CapabilityNotFoundError(CapabilityRegistryError):
    """Raised when a capability identifier cannot be found."""
