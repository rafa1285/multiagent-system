"""Provider-agnostic observability exceptions."""


class ObservabilityConfigError(RuntimeError):
    """Raised when observability provider configuration is invalid."""


class ObservabilityRequestError(RuntimeError):
    """Raised when provider request fails or returns an error."""
