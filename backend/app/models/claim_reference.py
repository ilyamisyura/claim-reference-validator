from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ClaimReference(Base):
    """
    Junction table linking claims to references (many-to-many).
    A claim can have 0, 1, or many references.
    A reference can support multiple claims.
    """

    __tablename__ = "claim_references"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    claim_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("claims.id", ondelete="CASCADE"), index=True
    )
    reference_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("references.id", ondelete="CASCADE"), index=True
    )

    # Optional: context about how this reference supports the claim
    relevance_score: Mapped[float | None] = mapped_column(
        nullable=True
    )  # AI-computed relevance
    context: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Why this ref supports this claim

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="CURRENT_TIMESTAMP",
    )

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="claim_references")
    reference: Mapped["Reference"] = relationship(
        "Reference", back_populates="claim_references"
    )
