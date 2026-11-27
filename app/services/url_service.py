"""
Business logic for creating, resolving, and inspecting short URLs.

Routers stay thin (parse request -> call service -> shape response) and
all the actual decision-making — duplicate alias checks, expiration
checks, click counting — lives here. This keeps the logic testable
without spinning up HTTP at all, and keeps it in one place if it ever
needs to change.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.url import Url
from app.services.base62 import encode
from app.utils.validators import is_reserved_alias

settings = get_settings()


class AliasAlreadyExistsError(Exception):
    """Raised when a requested custom alias is already taken."""


class ReservedAliasError(Exception):
    """Raised when a requested custom alias clashes with a reserved route."""


class UrlNotFoundError(Exception):
    """Raised when a short code does not correspond to any URL."""


class UrlGoneError(Exception):
    """Raised when a URL exists but has expired or been deactivated."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_short_url(short_code: str) -> str:
    return f"{settings.base_url.rstrip('/')}/{short_code}"


def create_short_url(
    db: Session,
    long_url: str,
    custom_alias: str | None,
    expires_in_hours: int | None,
) -> Url:
    """Create and persist a new shortened URL.

    If `custom_alias` is given, it is used directly as the short code
    (after checking it isn't reserved or already taken). Otherwise a
    row is inserted first so PostgreSQL assigns it an auto-incrementing
    ID, and that ID is Base62-encoded into the short code.
    """
    expires_at = None
    if expires_in_hours is not None:
        expires_at = _utcnow() + timedelta(hours=expires_in_hours)

    if custom_alias:
        if is_reserved_alias(custom_alias):
            raise ReservedAliasError(f"Alias '{custom_alias}' is reserved")

        existing = db.execute(
            select(Url).where(Url.short_code == custom_alias)
        ).scalar_one_or_none()
        if existing is not None:
            raise AliasAlreadyExistsError(f"Alias '{custom_alias}' already exists")

        url = Url(
            short_code=custom_alias,
            long_url=long_url,
            custom_alias=True,
            expires_at=expires_at,
        )
        db.add(url)
        db.commit()
        db.refresh(url)
        return url

    # No custom alias: insert first to obtain the auto-incrementing ID,
    # then derive the short code from that ID.
    url = Url(
        short_code="",  # placeholder, replaced right after flush
        long_url=long_url,
        custom_alias=False,
        expires_at=expires_at,
    )
    db.add(url)
    db.flush()  # assigns url.id without ending the transaction

    url.short_code = encode(url.id)
    db.commit()
    db.refresh(url)
    return url


def get_active_or_raise(db: Session, short_code: str) -> Url:
    """Fetch a URL by short code, raising if missing/expired/deactivated.

    Used by the redirect endpoint, where we need to distinguish "never
    existed" (404) from "existed but is no longer usable" (410).
    """
    url = db.execute(
        select(Url).where(Url.short_code == short_code)
    ).scalar_one_or_none()

    if url is None:
        raise UrlNotFoundError(f"Short code '{short_code}' not found")

    if not url.is_active:
        raise UrlGoneError(f"Short code '{short_code}' has been deactivated")

    if url.expires_at is not None and url.expires_at <= _utcnow():
        raise UrlGoneError(f"Short code '{short_code}' has expired")

    return url


def record_click(db: Session, url: Url) -> Url:
    """Increment the click count and update last_accessed_at for a URL."""
    url.click_count += 1
    url.last_accessed_at = _utcnow()
    db.commit()
    db.refresh(url)
    return url


def get_stats(db: Session, short_code: str) -> Url:
    """Fetch a URL by short code for the stats endpoint (no state check).

    Unlike `get_active_or_raise`, stats should be viewable even for an
    expired or deactivated URL, so this only checks existence.
    """
    url = db.execute(
        select(Url).where(Url.short_code == short_code)
    ).scalar_one_or_none()

    if url is None:
        raise UrlNotFoundError(f"Short code '{short_code}' not found")

    return url


def deactivate(db: Session, short_code: str) -> Url:
    """Mark a URL as inactive rather than deleting the row.

    Soft deletion preserves click history and stats for a URL even
    after it has been "removed", which is closer to how real link
    shorteners behave.
    """
    url = db.execute(
        select(Url).where(Url.short_code == short_code)
    ).scalar_one_or_none()

    if url is None:
        raise UrlNotFoundError(f"Short code '{short_code}' not found")

    url.is_active = False
    db.commit()
    db.refresh(url)
    return url


def to_short_url(url: Url) -> str:
    """Public helper so routers can build the full short URL string."""
    return _build_short_url(url.short_code)
