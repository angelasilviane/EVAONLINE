"""
Consolidate and merge all Alembic migrations into single head.
This script fixes the multiple head revisions issue.
"""

import os
from pathlib import Path

alembic_versions = Path("alembic/versions")

# Lista de migrações a reorganizar
migrations = [
    "001_create_initial_tables.py",
    "001_add_postgis_geometry.py",
    "002_add_cache_favorites_tables.py",
    "002_add_visitor_stats.py",
    "20251023_create_climate_history_tables.py",
]

print("=" * 80)
print("CONSOLIDANDO MIGRAÇÕES ALEMBIC")
print("=" * 80)

# Ler conteúdo de cada migração
migration_contents = {}
for m in migrations:
    path = alembic_versions / m
    if path.exists():
        with open(path, encoding="utf-8") as f:
            content = f.read()
        migration_contents[m] = content
        print(f"Lido: {m}")
    else:
        print(f"Nao encontrado: {m}")

# Criar única migração consolidada
consolidated = '''"""Consolidated migration - all initial setup

Revision ID: 001_consolidated
Revises: 
Create Date: 2025-11-03

Consolida todas as migrações iniciais em uma única.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_consolidated"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Cria todas as tabelas iniciais necessárias.
    """
    # =====================================================
    # Tabelas Principais
    # =====================================================
    
    op.create_table(
        'admin_users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )
    
    op.create_table(
        'user_session_cache',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('session_data', sa.JSON(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    
    op.create_table(
        'cache_metadata',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False, unique=True),
        sa.Column('ttl_seconds', sa.Integer(), nullable=False, server_default='3600'),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    op.create_table(
        'user_favorites',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    
    op.create_table(
        'favorite_location',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_favorite_id', sa.String(36), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_favorite_id'], ['user_favorites.id'], ),
    )
    
    op.create_table(
        'visitors',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('visited_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    op.create_table(
        'visitor_stats',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_visitors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_visitors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('return_visitors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    
    op.create_table(
        'eto_results',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('location_id', sa.String(36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('eto_value', sa.Float(), nullable=False),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('cached', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """
    Remove todas as tabelas.
    """
    op.drop_table('eto_results')
    op.drop_table('visitor_stats')
    op.drop_table('visitors')
    op.drop_table('favorite_location')
    op.drop_table('user_favorites')
    op.drop_table('cache_metadata')
    op.drop_table('user_session_cache')
    op.drop_table('admin_users')
'''

# Backup das antigas
print("\nBackup de migrações antigas...")
for m in migrations:
    path = alembic_versions / m
    if path.exists():
        backup_name = f"{m}.backup"
        backup_path = alembic_versions / backup_name
        os.rename(path, backup_path)
        print(f"  Backup: {m} -> {backup_name}")

# Criar consolidada
consolidated_path = alembic_versions / "001_consolidated_migration.py"
with open(consolidated_path, "w", encoding="utf-8") as f:
    f.write(consolidated)

print(f"\n✅ Criado: 001_consolidated_migration.py")
print(f"\nProximo passo: docker-compose run --rm test-runner")
print("=" * 80)
