from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Reference(Base):
    """
    Independent reference table.
    References are deduplicated across all projects by DOI, title, and authors.
    """

    __tablename__ = "references"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Identifiers for deduplication
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str] = mapped_column(Text)  # JSON or comma-separated
    source: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Journal, conference, etc.
    year: Mapped[int | None] = mapped_column(nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # For deduplication: hash of normalized title + first author
    dedup_hash: Mapped[str] = mapped_column(String(64), index=True, unique=True)

    # Embeddings and processing metadata
    embedding_vector: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON-encoded vector
    is_processed: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="CURRENT_TIMESTAMP",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="CURRENT_TIMESTAMP",
    )

    # Relationships
    claim_references: Mapped[list["ClaimReference"]] = relationship(
        "ClaimReference", back_populates="reference", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_reference_title_authors", "title", "authors"),
    )
