from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Claim(Base):
    """
    Claims extracted from project documents.
    Each claim belongs to exactly one project.
    """

    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    # Claim content
    text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # e.g., "factual", "statistical", etc.

    # Position in document (optional, for tracking)
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    paragraph_index: Mapped[int | None] = mapped_column(nullable=True)

    # Verification status
    verification_status: Mapped[str] = mapped_column(
        String(32), default="unverified"
    )  # unverified, verified, disputed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="CURRENT_TIMESTAMP",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="CURRENT_TIMESTAMP",
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="claims")
    claim_references: Mapped[list["ClaimReference"]] = relationship(
        "ClaimReference", back_populates="claim", cascade="all, delete-orphan"
    )
