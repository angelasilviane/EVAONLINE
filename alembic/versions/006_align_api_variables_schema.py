"""Align api_variables table with APIVariables model

Revision ID: 006_align_api_variables
Revises: 005_update_climate_data
Create Date: 2025-11-07 19:25:00.000000

Changes:
- Rename column api_name → source_api
- Add columns: standard_name, is_required_for_eto
- Update indexes and constraints
- Migrate existing data
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006_align_api_variables"
down_revision: Union[str, None] = "005_update_climate_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Align api_variables table with APIVariables model."""

    print("\n🔧 Alinhando tabela api_variables com o modelo...")

    # 1. Drop existing indexes and constraints that reference api_name
    print("   - Removendo constraints e índices antigos...")
    op.drop_constraint("uq_api_variable", "api_variables", type_="unique")
    op.drop_index("idx_api_variables_api", table_name="api_variables")

    # 2. Rename api_name → source_api
    print("   - Renomeando api_name → source_api...")
    op.alter_column(
        "api_variables",
        "api_name",
        new_column_name="source_api",
        existing_type=sa.String(50),
        nullable=False,
    )

    # 3. Add new columns
    print("   - Adicionando colunas: standard_name, is_required_for_eto...")

    # Add standard_name (nullable first, will update then make NOT NULL)
    op.add_column(
        "api_variables",
        sa.Column(
            "standard_name",
            sa.String(100),
            nullable=True,
            comment="Nome padronizado interno (temp_max_c, etc.)",
        ),
    )

    # Set default values: use mapping column if exists, else variable_name
    op.execute(
        """
        UPDATE api_variables 
        SET standard_name = COALESCE(mapping, variable_name)
    """
    )

    # Now make it NOT NULL
    op.alter_column("api_variables", "standard_name", nullable=False)

    # Add is_required_for_eto with default False
    op.add_column(
        "api_variables",
        sa.Column(
            "is_required_for_eto",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Se a variável é essencial para cálculo de ETo",
        ),
    )

    # 4. Update existing description to be nullable and larger
    print("   - Atualizando coluna description...")
    op.alter_column(
        "api_variables",
        "description",
        type_=sa.String(500),
        existing_type=sa.Text(),
        nullable=True,
    )

    # 5. Update unit to NOT NULL
    print("   - Atualizando coluna unit...")
    # First set a default for any null values
    op.execute("UPDATE api_variables SET unit = 'unknown' WHERE unit IS NULL")
    op.alter_column(
        "api_variables", "unit", nullable=False, existing_type=sa.String(50)
    )

    # 6. Recreate indexes and constraints with new column names
    print("   - Recriando constraints e índices...")
    op.create_unique_constraint(
        "uq_api_variable", "api_variables", ["source_api", "variable_name"]
    )

    op.create_index("idx_source_api", "api_variables", ["source_api"])

    op.create_index("idx_standard_name", "api_variables", ["standard_name"])

    op.create_index(
        "idx_required_eto", "api_variables", ["is_required_for_eto"]
    )

    print("\n✅ api_variables alinhada com o modelo APIVariables")
    print("   - api_name → source_api ✓")
    print("   - +2 colunas: standard_name, is_required_for_eto ✓")
    print("   - Índices e constraints atualizados ✓")


def downgrade() -> None:
    """Revert api_variables to old schema."""

    print("\n🔙 Revertendo api_variables para schema antigo...")

    # 1. Drop new indexes
    op.drop_index("idx_required_eto", table_name="api_variables")
    op.drop_index("idx_standard_name", table_name="api_variables")
    op.drop_index("idx_source_api", table_name="api_variables")
    op.drop_constraint("uq_api_variable", "api_variables", type_="unique")

    # 2. Remove new columns
    op.drop_column("api_variables", "is_required_for_eto")
    op.drop_column("api_variables", "standard_name")

    # 3. Rename source_api → api_name
    op.alter_column(
        "api_variables",
        "source_api",
        new_column_name="api_name",
        existing_type=sa.String(50),
        nullable=False,
    )

    # 4. Revert description changes
    op.alter_column(
        "api_variables",
        "description",
        type_=sa.Text(),
        existing_type=sa.String(500),
        nullable=True,
    )

    # 5. Revert unit to nullable
    op.alter_column(
        "api_variables", "unit", nullable=True, existing_type=sa.String(50)
    )

    # 6. Recreate old indexes
    op.create_unique_constraint(
        "uq_api_variable", "api_variables", ["api_name", "variable_name"]
    )

    op.create_index("idx_api_variables_api", "api_variables", ["api_name"])

    print("✅ Revertido para schema antigo")
