#!/usr/bin/env python3
"""
💾 TESTE DE BANCO DE DADOS - EVAonline
======================================
Testa operações do banco de dados:
- Criação de tabelas
- Operações CRUD
- Transações
- Constraints

Uso:
    python backend/tests/test_database.py

Testa:
- Schema e tabelas
- Inserções
- Atualizações
- Deleções
- Queries
- Integridade referencial
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

# Adicionar raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Cores
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

results = {"passed": 0, "failed": 0, "warnings": 0}


def header(text):
    """Print section header."""
    print(f"\n{CYAN}{BOLD}{'='*80}{RESET}")
    print(f"{CYAN}{BOLD}{text}{RESET}")
    print(f"{CYAN}{BOLD}{'='*80}{RESET}\n")


def success(msg, detail=""):
    """Print success message."""
    print(f"{GREEN}✅ {msg}{RESET}", end="")
    if detail:
        print(f" | {detail}")
    else:
        print()
    results["passed"] += 1


def failed(msg, detail=""):
    """Print failed message."""
    print(f"{RED}❌ {msg}{RESET}", end="")
    if detail:
        print(f" | {detail[:60]}")
    else:
        print()
    results["failed"] += 1


def warning_msg(msg, detail=""):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {msg}{RESET}", end="")
    if detail:
        print(f" | {detail[:60]}")
    else:
        print()
    results["warnings"] += 1


# ============================================================================
# TESTE 1: CONEXÃO E SCHEMA
# ============================================================================


def test_connection_and_schema() -> None:
    """Test database connection and schema."""
    header("TESTE 1: CONEXÃO E SCHEMA DO BANCO")

    try:
        from backend.database.connection import engine, SessionLocal

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            if version:
                success("Conexão PostgreSQL", f"Versão: {version[:40]}")
            else:
                failed("Conexão PostgreSQL", "sem versão")

        # List tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if tables:
            success(f"Tabelas encontradas: {len(tables)}")
            print(f"\n   📋 Tabelas do banco:")
            for table in sorted(tables)[:20]:
                cols = inspector.get_columns(table)
                print(f"      • {table} ({len(cols)} colunas)")
        else:
            warning_msg("Nenhuma tabela", "Execute alembic upgrade head")

        # Test session
        session = SessionLocal()
        session.close()
        success("SessionLocal funcionando")

    except Exception as e:
        failed("Schema check", str(e)[:60])


# ============================================================================
# TESTE 2: VISITOR STATS OPERATIONS
# ============================================================================


def test_visitor_stats() -> None:
    """Test visitor stats CRUD operations."""
    header("TESTE 2: OPERAÇÕES VISITOR_STATS")

    try:
        from backend.database.models.visitor_stats import VisitorStats
        from backend.database.connection import SessionLocal

        session = SessionLocal()

        # Count before
        count_before = session.query(VisitorStats).count()
        success(f"Registros atuais", f"Total: {count_before}")

        # Insert test record
        try:
            test_stat = VisitorStats(
                date=datetime.now().date(),
                path="/test",
                method="GET",
                status_code=200,
                response_time_ms=100.5,
                ip_address="127.0.0.1",
            )
            session.add(test_stat)
            session.commit()
            success("INSERT", "Novo registro VisitorStats criado")

            stat_id = test_stat.id
            count_after = session.query(VisitorStats).count()
            success("SELECT", f"Total após insert: {count_after}")

            # Update record
            stmt = text(
                "UPDATE visitor_stats SET status_code = :status "
                "WHERE id = :id"
            )
            session.execute(stmt, {"status": 201, "id": stat_id})
            session.commit()
            success("UPDATE", f"Registro {stat_id} atualizado")

            # Delete record
            session.query(VisitorStats).filter(
                VisitorStats.id == stat_id
            ).delete()
            session.commit()
            success("DELETE", f"Registro {stat_id} deletado")

        except IntegrityError as e:
            session.rollback()
            warning_msg("Integrity constraint", str(e)[:60])
        except Exception as e:
            session.rollback()
            failed("CRUD operations", str(e)[:60])
        finally:
            session.close()

    except Exception as e:
        failed("Visitor stats test", str(e)[:60])


# ============================================================================
# TESTE 3: USER FAVORITES OPERATIONS
# ============================================================================


def test_user_favorites() -> None:
    """Test user favorites CRUD operations."""
    header("TESTE 3: OPERAÇÕES USER_FAVORITES")

    try:
        from backend.database.models.user_favorites import (
            UserFavorites,
            FavoriteLocation,
        )
        from backend.database.connection import SessionLocal

        session = SessionLocal()

        count_before = session.query(UserFavorites).count()
        success(f"Favorites atuais", f"Total: {count_before}")

        # Create user favorites collection
        try:
            user_fav = UserFavorites(
                session_id="test_session_123",
                user_id="test_user_456",
            )
            session.add(user_fav)
            session.flush()

            success("INSERT", "UserFavorites collection criada")

            # Create favorite location
            fav_loc = FavoriteLocation(
                favorites_id=user_fav.id,
                latitude=-15.0,
                longitude=-48.0,
                name="Brasília - Teste",
                category="Capital",
                created_at=datetime.now(),
            )
            session.add(fav_loc)
            session.commit()
            success("INSERT", "FavoriteLocation adicionada")

            # Query
            favorites = (
                session.query(UserFavorites)
                .filter(UserFavorites.session_id == "test_session_123")
                .first()
            )

            if favorites:
                locations = (
                    session.query(FavoriteLocation)
                    .filter(FavoriteLocation.favorites_id == favorites.id)
                    .all()
                )
                success("SELECT", f"Encontradas {len(locations)} localizações")

            # Cleanup
            session.query(FavoriteLocation).filter(
                FavoriteLocation.favorites_id == user_fav.id
            ).delete()
            session.query(UserFavorites).filter(
                UserFavorites.id == user_fav.id
            ).delete()
            session.commit()
            success("DELETE", "Registros de favoritos deletados")

        except IntegrityError as e:
            session.rollback()
            warning_msg("Referential integrity", str(e)[:60])
        except Exception as e:
            session.rollback()
            failed("Favorites CRUD", str(e)[:60])
        finally:
            session.close()

    except ImportError:
        warning_msg("Favorites models", "Modelos não disponíveis")
    except Exception as e:
        failed("Favorites test", str(e)[:60])


# ============================================================================
# TESTE 4: CACHE OPERATIONS
# ============================================================================


def test_cache_operations() -> None:
    """Test cache operations."""
    header("TESTE 4: OPERAÇÕES CACHE")

    try:
        from backend.database.models.user_cache import UserSessionCache

        from backend.database.connection import SessionLocal

        session = SessionLocal()

        try:
            # Create cache record
            cache = UserSessionCache(
                session_id="test_cache_123",
                user_id="test_user_789",
                data='{"test": "data"}',
                expires_at=datetime.now() + timedelta(hours=1),
            )
            session.add(cache)
            session.commit()
            success("INSERT", "Cache entry criada")

            cache_id = cache.id

            # Read cache
            cached = (
                session.query(UserSessionCache)
                .filter(UserSessionCache.id == cache_id)
                .first()
            )

            if cached and cached.data:
                success("SELECT", "Cache entry recuperada")

            # Update cache
            cached.data = '{"updated": true}'
            session.commit()
            success("UPDATE", "Cache entry atualizada")

            # Delete cache
            session.query(UserSessionCache).filter(
                UserSessionCache.id == cache_id
            ).delete()
            session.commit()
            success("DELETE", "Cache entry deletada")

        except Exception as e:
            session.rollback()
            failed("Cache CRUD", str(e)[:60])
        finally:
            session.close()

    except ImportError:
        warning_msg("Cache models", "Modelos não disponíveis")
    except Exception as e:
        failed("Cache test", str(e)[:60])


# ============================================================================
# TESTE 5: QUERY PERFORMANCE
# ============================================================================


def test_query_performance() -> None:
    """Test query performance and indexing."""
    header("TESTE 5: PERFORMANCE DE QUERIES")

    try:
        from backend.database.connection import engine

        inspector = inspect(engine)

        # Check indexes
        tables = inspector.get_table_names()
        total_indexes = 0

        for table in tables:
            indexes = inspector.get_indexes(table)
            total_indexes += len(indexes)

        if total_indexes > 0:
            success(f"Índices encontrados: {total_indexes}")
        else:
            warning_msg("Índices", "Nenhum índice encontrado")

        # Test simple query
        start = datetime.now()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM visitor_stats"))
            count = result.scalar()
            duration = (datetime.now() - start).total_seconds() * 1000
            success(
                "Query performance", f"{count} registros em {duration:.2f}ms"
            )

    except Exception as e:
        warning_msg("Performance test", str(e)[:60])


# ============================================================================
# TESTE 6: TRANSACTION HANDLING
# ============================================================================


def test_transactions() -> None:
    """Test transaction handling."""
    header("TESTE 6: TRANSAÇÕES")

    try:
        from backend.database.models.visitor_stats import VisitorStats
        from backend.database.connection import SessionLocal

        session = SessionLocal()

        try:
            # Transaction test
            stat1 = VisitorStats(
                date=datetime.now().date(),
                path="/tx_test_1",
                method="GET",
                status_code=200,
                response_time_ms=50.0,
                ip_address="127.0.0.1",
            )
            stat2 = VisitorStats(
                date=datetime.now().date(),
                path="/tx_test_2",
                method="POST",
                status_code=201,
                response_time_ms=75.0,
                ip_address="127.0.0.1",
            )
            session.add_all([stat1, stat2])
            session.commit()
            success("TRANSACTION", "Múltiplos inserts em uma transação")

            # Cleanup
            session.query(VisitorStats).filter(
                VisitorStats.path.like("/tx_test%")
            ).delete()
            session.commit()
            success("TRANSACTION", "Cleanup após teste")

        except Exception as e:
            session.rollback()
            failed("Transactions", str(e)[:60])
        finally:
            session.close()

    except Exception as e:
        failed("Transaction test", str(e)[:60])


# ============================================================================
# TESTE 7: DATA INTEGRITY
# ============================================================================


def test_data_integrity() -> None:
    """Test data integrity constraints."""
    header("TESTE 7: INTEGRIDADE DOS DADOS")

    try:
        from backend.database.connection import engine

        with engine.connect() as conn:
            # Check foreign keys
            result = conn.execute(
                text(
                    "SELECT constraint_name FROM information_schema."
                    "table_constraints WHERE constraint_type = 'FOREIGN KEY'"
                )
            )
            fk_count = len(result.fetchall())

            if fk_count > 0:
                success(f"Foreign keys: {fk_count}")
            else:
                warning_msg("Foreign keys", "Nenhuma FK encontrada")

            # Check unique constraints
            result = conn.execute(
                text(
                    "SELECT constraint_name FROM information_schema."
                    "table_constraints WHERE constraint_type = 'UNIQUE'"
                )
            )
            unique_count = len(result.fetchall())

            if unique_count > 0:
                success(f"Unique constraints: {unique_count}")
            else:
                warning_msg("Unique constraints", "Nenhuma constraint")

    except Exception as e:
        warning_msg("Data integrity check", str(e)[:60])


# ============================================================================
# RESUMO
# ============================================================================


def print_summary():
    """Print final summary."""
    header("📊 RESUMO DOS TESTES DE BANCO DE DADOS")

    total = results["passed"] + results["failed"] + results["warnings"]
    pass_pct = (results["passed"] / total * 100) if total > 0 else 0

    print(f"{GREEN}✅ Passou:{RESET} {results['passed']}")
    print(f"{RED}❌ Falhou:{RESET} {results['failed']}")
    print(f"{YELLOW}⚠️  Avisos:{RESET} {results['warnings']}")
    pct_str = f"({pass_pct:.1f}%)"
    print(f"\n{BOLD}Total: {results['passed']}/{total} {pct_str}{RESET}\n")

    sep = "=" * 80
    print(f"{BOLD}{sep}{RESET}")
    if results["failed"] == 0:
        status = "✅ BANCO DE DADOS ESTÁ SAUDÁVEL!"
        print(f"{GREEN}{BOLD}{status}{RESET}\n")
    else:
        status = "❌ PROBLEMAS ENCONTRADOS NO BANCO"
        print(f"{RED}{BOLD}{status}{RESET}\n")
    print(f"{BOLD}{sep}{RESET}\n")


# ============================================================================
# MAIN
# ============================================================================


def main() -> None:
    """Execute database tests."""
    print(f"\n{BOLD}{BLUE}EVAonline - TESTE DE BANCO DE DADOS{RESET}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    try:
        test_connection_and_schema()
        test_visitor_stats()
        test_user_favorites()
        test_cache_operations()
        test_query_performance()
        test_transactions()
        test_data_integrity()

        print_summary()

    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Teste interrompido{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}{BOLD}❌ Erro:{RESET} {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
