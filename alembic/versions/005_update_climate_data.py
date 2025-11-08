"""
Update climate_data table schema.

Revision ID: 005_update_climate_data
Revises: 004_climate_infra
Create Date: 2025-11-07

Changes:
- Add elevation, timezone, quality_flags, processing_metadata columns
- Remove quality_score column
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "005_update_climate_data"
down_revision = "004_climate_infra"
branch_labels = None
depends_on = None


def upgrade():
    """Add new columns and remove quality_score."""
    print("\n🔧 Atualizando tabela climate_data...")

    # Add new columns
    op.add_column(
        "climate_data", sa.Column("elevation", sa.Float(), nullable=True)
    )
    op.add_column(
        "climate_data", sa.Column("timezone", sa.String(50), nullable=True)
    )
    op.add_column(
        "climate_data",
        sa.Column("quality_flags", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "climate_data",
        sa.Column("processing_metadata", postgresql.JSONB(), nullable=True),
    )

    # Migrate data if exists
    op.execute(
        """
        UPDATE climate_data
        SET quality_flags = jsonb_build_object('score', quality_score)
        WHERE quality_score IS NOT NULL
    """
    )

    # Drop old column
    op.drop_column("climate_data", "quality_score")

    print("✅ climate_data atualizada: +4 colunas, -1 coluna (quality_score)")


def downgrade():
    """Revert changes."""
    print("\n🔙 Revertendo climate_data...")

    # Add back quality_score
    op.add_column(
        "climate_data", sa.Column("quality_score", sa.Float(), nullable=True)
    )

    # Migrate data back
    op.execute(
        """
        UPDATE climate_data
        SET quality_score = (quality_flags->>'score')::float
        WHERE quality_flags IS NOT NULL
    """
    )

    # Drop new columns
    op.drop_column("climate_data", "processing_metadata")
    op.drop_column("climate_data", "quality_flags")
    op.drop_column("climate_data", "timezone")
    op.drop_column("climate_data", "elevation")

    print("✅ Reversão concluída")
