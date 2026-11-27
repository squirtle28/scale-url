"""
Routes for creating short URLs, viewing stats, deactivating URLs, and
redirecting short codes to their original destination.

Each route function stays a thin translation layer: parse the request,
delegate to `app.services.url_service`, translate any domain exception
into the right HTTP status code, and shape the response.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.url import (
    MessageResponse,
    UrlCreateRequest,
    UrlCreateResponse,
    UrlStatsResponse,
)
from app.services import url_service
from app.services.url_service import (
    AliasAlreadyExistsError,
    ReservedAliasError,
    UrlGoneError,
    UrlNotFoundError,
)

# Endpoints under /api/v1/urls: creation, stats, deactivation.
router = APIRouter(prefix="/api/v1/urls", tags=["urls"])

# The redirect lives at the bare root path (GET /{short_code}), separate
# from the /api/v1 namespace, so it needs its own router with no prefix.
redirect_router = APIRouter(tags=["redirect"])


@router.post(
    "",
    response_model=UrlCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_url(
    payload: UrlCreateRequest, db: Session = Depends(get_db)
) -> UrlCreateResponse:
    """Create a new shortened URL, optionally with a custom alias and/or
    an expiration window."""
    try:
        url = url_service.create_short_url(
            db=db,
            long_url=str(payload.long_url),
            custom_alias=payload.custom_alias,
            expires_in_hours=payload.expires_in_hours,
        )
    except ReservedAliasError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except AliasAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return UrlCreateResponse(
        short_code=url.short_code,
        short_url=url_service.to_short_url(url),
        long_url=url.long_url,
        expires_at=url.expires_at,
        created_at=url.created_at,
    )


@router.get("/{short_code}/stats", response_model=UrlStatsResponse)
def get_url_stats(short_code: str, db: Session = Depends(get_db)) -> UrlStatsResponse:
    """Return usage statistics for a short code, whether or not it is
    currently active/expired — stats remain viewable either way."""
    try:
        url = url_service.get_stats(db, short_code)
    except UrlNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return UrlStatsResponse(
        short_code=url.short_code,
        long_url=url.long_url,
        total_clicks=url.click_count,
        created_at=url.created_at,
        last_accessed_at=url.last_accessed_at,
        expires_at=url.expires_at,
        is_active=url.is_active,
    )


@router.delete("/{short_code}", response_model=MessageResponse)
def delete_url(short_code: str, db: Session = Depends(get_db)) -> MessageResponse:
    """Deactivate a URL. This is a soft delete: the row and its click
    history are kept, but the short code stops resolving."""
    try:
        url_service.deactivate(db, short_code)
    except UrlNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return MessageResponse(message=f"Short code '{short_code}' has been deactivated")


@redirect_router.get("/{short_code}")
def redirect_to_long_url(
    short_code: str, db: Session = Depends(get_db)
) -> RedirectResponse:
    """Resolve a short code and redirect the client to the original URL.

    Returns 404 if the code was never created, 410 if it exists but has
    expired or been deactivated, and a 302 redirect otherwise.
    """
    try:
        url = url_service.get_active_or_raise(db, short_code)
    except UrlNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except UrlGoneError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail=str(exc)
        ) from exc

    url_service.record_click(db, url)
    return RedirectResponse(url=url.long_url, status_code=status.HTTP_302_FOUND)
