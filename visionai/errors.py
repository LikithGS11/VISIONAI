"""Error types with messages that are safe to show to end users."""


class VisionAIError(Exception):
    """Base error. `str(err)` is always a user-friendly message."""

    status_code = 500


class InvalidInputError(VisionAIError):
    """The user sent something we can't process (bad image, empty text...)."""

    status_code = 400


class ConfigError(VisionAIError):
    """A required setting or system dependency is missing."""

    status_code = 503


class ProviderError(VisionAIError):
    """An external service (Gemini, OpenRouteService, geocoder, TTS) failed."""

    status_code = 502


class RateLimitError(ProviderError):
    status_code = 429
