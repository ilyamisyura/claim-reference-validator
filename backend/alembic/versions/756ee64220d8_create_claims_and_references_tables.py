"""Create claims and references tables

Revision ID: 756ee64220d8
Revises: f9c4a366ea82
Create Date: 2026-01-02 17:09:07.015707

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_claims_refs"
down_revision: Union[str, Sequence[str], None] = "f9c4a366ea82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add document fields to projects table
    op.add_column("projects", sa.Column("document_path", sa.Text(), nullable=True))
    op.add_column(
        "projects", sa.Column("document_filename", sa.String(length=255), nullable=True)
    )

    # Create references table
    op.create_table(
        "references",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("doi", sa.String(length=255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("dedup_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding_vector", sa.Text(), nullable=True),
        sa.Column(
            "is_processed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_references_doi", "references", ["doi"])
    op.create_index(
        "ix_references_dedup_hash", "references", ["dedup_hash"], unique=True
    )
    op.create_index("ix_reference_title_authors", "references", ["title", "authors"])

    # Create claims table
    op.create_table(
        "claims",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=64), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("paragraph_index", sa.Integer(), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'unverified'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_claims_project_id", "claims", ["project_id"])

    # Create claim_references junction table
    op.create_table(
        "claim_references",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("claim_id", sa.BigInteger(), nullable=False),
        sa.Column("reference_id", sa.BigInteger(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["reference_id"], ["references.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_claim_references_claim_id", "claim_references", ["claim_id"])
    op.create_index(
        "ix_claim_references_reference_id", "claim_references", ["reference_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Drop claim_references table
    op.drop_index("ix_claim_references_reference_id", table_name="claim_references")
    op.drop_index("ix_claim_references_claim_id", table_name="claim_references")
    op.drop_table("claim_references")

    # Drop claims table
    op.drop_index("ix_claims_project_id", table_name="claims")
    op.drop_table("claims")

    # Drop references table
    op.drop_index("ix_reference_title_authors", table_name="references")
    op.drop_index("ix_references_dedup_hash", table_name="references")
    op.drop_index("ix_references_doi", table_name="references")
    op.drop_table("references")

    # Remove document fields from projects table
    op.drop_column("projects", "document_filename")
    op.drop_column("projects", "document_path")
