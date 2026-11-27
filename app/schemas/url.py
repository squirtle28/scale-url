"""Pydantic request/response models for the URL endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class UrlCreateRequest(BaseModel):
    """Payload for POST /api/v1/urls."""

    long_url: HttpUrl = Field(..., description="The original URL to shorten.")
    custom_alias: str | None = Field(
        default=None,
        min_length=3,
        max_length=20,
        description="Optional custom short code. Alphanumeric, - and _ only.",
    )
    expires_in_hours: int | None = Field(
        default=None,
        ge=1,
        le=8760,  # 1 year
        description="Hours until the URL expires. Omit for no expiration.",
    )

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "custom_alias may only contain letters, digits, '-' and '_'"
            )
        return value


class UrlCreateResponse(BaseModel):
    """Response for a successfully created short URL."""

    short_code: str
    short_url: str
    long_url: str
    expires_at: datetime | None
    created_at: datetime


class UrlStatsResponse(BaseModel):
    """Response for GET /api/v1/urls/{short_code}/stats."""

    short_code: str
    long_url: str
    total_clicks: int
    created_at: datetime
    last_accessed_at: datetime | None
    expires_at: datetime | None
    is_active: bool


class MessageResponse(BaseModel):
    """Generic message response, used for deletion confirmation etc."""

    message: str
