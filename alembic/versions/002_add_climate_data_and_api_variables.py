"""Add climate_data and api_variables tables

Revision ID: 002_climate_multi_api
Revises: 001_consolidated
Create Date: 2025-11-06

Adiciona suporte para múltiplas APIs climáticas:
- Tabela climate_data: Armazenamento flexível com JSONB
- Tabela api_variables: Mapeamento de variáveis por API
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_climate_multi_api"
down_revision: Union[str, None] = "001_consolidated"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Cria tabelas para suporte multi-API de dados climáticos.
    """

    # =========================================================================
    # Tabela: climate_data
    # =========================================================================
    op.create_table(
        "climate_data",
        # Identificação
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "source_api",
            sa.String(length=50),
            nullable=False,
            comment="Fonte da API",
        ),
        # Localização
        sa.Column(
            "latitude",
            sa.Float(),
            nullable=False,
            comment="Latitude em graus decimais",
        ),
        sa.Column(
            "longitude",
            sa.Float(),
            nullable=False,
            comment="Longitude em graus decimais",
        ),
        sa.Column(
            "elevation",
            sa.Float(),
            nullable=True,
            comment="Elevação em metros (crucial para ETo)",
        ),
        sa.Column(
            "timezone",
            sa.String(length=50),
            nullable=True,
            comment="Timezone IANA (ex: America/Sao_Paulo)",
        ),
        # Temporal
        sa.Column(
            "date",
            sa.DateTime(),
            nullable=False,
            comment="Data dos dados climáticos",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment="Data de criação do registro",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            onupdate=sa.func.now(),
            comment="Data de atualização",
        ),
        # Dados Climáticos (JSONB - Flexível)
        sa.Column(
            "raw_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Dados originais da API em formato nativo",
        ),
        sa.Column(
            "harmonized_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Dados harmonizados em formato padronizado",
        ),
        # Resultado ETo
        sa.Column(
            "eto_mm_day",
            sa.Float(),
            nullable=True,
            comment="Evapotranspiração de referência (mm/dia)",
        ),
        sa.Column(
            "eto_method",
            sa.String(length=20),
            nullable=True,
            server_default="penman_monteith",
            comment="Método de cálculo de ETo",
        ),
        # Metadados
        sa.Column(
            "quality_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Flags de qualidade: missing_data, interpolated",
        ),
        sa.Column(
            "processing_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Metadados: versão, tempo de processamento, etc.",
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    # Índices para climate_data
    op.create_index(
        "idx_climate_location_date",
        "climate_data",
        ["latitude", "longitude", "date"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_climate_source_date",
        "climate_data",
        ["source_api", "date"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_climate_date",
        "climate_data",
        ["date"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_climate_source_api",
        "climate_data",
        ["source_api"],
        unique=False,
        schema="public",
    )

    # =========================================================================
    # Tabela: api_variables
    # =========================================================================
    op.create_table(
        "api_variables",
        # Identificação
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # Mapeamento API
        sa.Column(
            "source_api",
            sa.String(length=50),
            nullable=False,
            comment="API fonte (nasa_power, openmeteo_archive, etc.)",
        ),
        sa.Column(
            "variable_name",
            sa.String(length=100),
            nullable=False,
            comment="Nome da variável na API original",
        ),
        # Padronização
        sa.Column(
            "standard_name",
            sa.String(length=100),
            nullable=False,
            comment="Nome padronizado interno (temp_max_c, etc.)",
        ),
        sa.Column(
            "unit",
            sa.String(length=50),
            nullable=False,
            comment="Unidade de medida (°C, m/s, MJ/m²/d, etc.)",
        ),
        sa.Column(
            "description",
            sa.String(length=500),
            nullable=True,
            comment="Descrição legível da variável climática",
        ),
        # Flags
        sa.Column(
            "is_required_for_eto",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Se a variável é essencial para cálculo de ETo",
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_api", "variable_name", name="uq_api_variable"
        ),
        schema="public",
    )

    # Índices para api_variables
    op.create_index(
        "idx_source_api",
        "api_variables",
        ["source_api"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_standard_name",
        "api_variables",
        ["standard_name"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_required_eto",
        "api_variables",
        ["is_required_for_eto"],
        unique=False,
        schema="public",
    )

    print("✅ Tabelas climate_data e api_variables criadas com sucesso!")
    print("📝 Execute o seed: python database/seeds/api_variables_seed.py")


def downgrade() -> None:
    """
    Remove tabelas de suporte multi-API.
    """

    # Remove índices de api_variables
    op.drop_index("idx_required_eto", table_name="api_variables")
    op.drop_index("idx_standard_name", table_name="api_variables")
    op.drop_index("idx_source_api", table_name="api_variables")

    # Remove tabela api_variables
    op.drop_table("api_variables", schema="public")

    # Remove índices de climate_data
    op.drop_index("idx_climate_source_api", table_name="climate_data")
    op.drop_index("idx_climate_date", table_name="climate_data")
    op.drop_index("idx_climate_source_date", table_name="climate_data")
    op.drop_index("idx_climate_location_date", table_name="climate_data")

    # Remove tabela climate_data
    op.drop_table("climate_data", schema="public")

    print("⚠️  Tabelas climate_data e api_variables removidas!")
