"""Small validation helpers shared across the app."""

# Short codes that would collide with existing API routes if allowed as
# custom aliases (e.g. someone requesting alias "health" or "api").
RESERVED_ALIASES = {"api", "health", "docs", "openapi.json", "redoc", "favicon.ico"}


def is_reserved_alias(alias: str) -> bool:
    """Return True if `alias` would clash with a reserved route."""
    return alias.lower() in RESERVED_ALIASES
