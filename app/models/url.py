"""SQLAlchemy model for shortened URLs."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Url(Base):
    """A single shortened URL record.

    `id` is the auto-incrementing primary key that gets Base62-encoded
    into the public-facing `short_code` when no custom alias is given.
    """

    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    short_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    long_url: Mapped[str] = mapped_column(Text, nullable=False)
    custom_alias: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    click_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return f"<Url id={self.id} short_code={self.short_code!r}>"
