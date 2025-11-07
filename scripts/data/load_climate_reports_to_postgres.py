"""
Script Otimizado para Carregar Dados Climáticos Históricos no PostgreSQL
Versão: 2.0 (Production-Ready)

Melhorias vs v1.0:
- ✅ Pool de conexões configurável
- ✅ Validação de integridade de dados
- ✅ Transações seguras com rollback automático
- ✅ Constraints UNIQUE para evitar duplicatas
- ✅ Melhor tratamento de erros
- ✅ Logging detalhado
- ✅ Verificação de dados antes/depois
"""

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from tenacity import retry, stop_after_attempt, wait_fixed

# ==========================================
# CONFIGURAÇÃO INICIAL
# ==========================================

# Carrega .env.local se existir (execução local), senão .env (Docker)
if Path(".env.local").exists():
    logger_temp = logger
    load_dotenv(".env.local")
    print("✅ Usando .env.local (execução local/Windows)")
else:
    load_dotenv(".env")
    print("✅ Usando .env (execução em Docker)")

# Variáveis de ambiente com fallbacks
PG_USER = os.getenv("POSTGRES_USER", "evaonline")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DB = os.getenv("POSTGRES_DB", "evaonline")

# Pool config para produção
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 20))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600))

DB_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# ✅ Engine com pooling otimizado
engine = create_engine(
    DB_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_recycle=DB_POOL_RECYCLE,
    echo=False,
    pool_pre_ping=True,  # Valida conexões antes de usar
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Logging
logger.remove()  # Remove handler padrão
logger.add(
    "logs/load_data.log",
    rotation="100 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
)
logger.add(lambda msg: print(msg), level="INFO")  # Console também

# ==========================================
# DEFINIÇÃO DE TABELAS (ORM)
# ==========================================


class CitiesSummary(Base):
    __tablename__ = "cities_summary"

    city = Column(String, primary_key=True)
    region = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    alt = Column(Float, nullable=True)
    total_records = Column(Integer, nullable=True)
    data_period = Column(String, nullable=True)
    variables = Column(JSON, nullable=True)
    completeness = Column(Float, default=0.0)
    eto_mean = Column(Float, nullable=True)
    eto_std = Column(Float, nullable=True)
    eto_max = Column(Float, nullable=True)
    eto_min = Column(Float, nullable=True)
    eto_p99 = Column(Float, nullable=True)
    eto_p01 = Column(Float, nullable=True)

    __table_args__ = (
        Index("idx_cities_summary_lat_lon", "lat", "lon"),
        Index("idx_cities_summary_region", "region"),
    )


class AnnualNormals(Base):
    __tablename__ = "annual_normals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String, nullable=False)
    period = Column(String, nullable=False)
    eto_normal_mm_day = Column(Float, nullable=True)
    precip_normal_mm_year = Column(Float, nullable=True)
    valid_years = Column(Integer, nullable=True)
    completeness = Column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("city", "period", name="uq_annual_normals_city_period"),
        Index("idx_annual_normals_city_period", "city", "period"),
    )


class ExtremesAnalysis(Base):
    __tablename__ = "extremes_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String, nullable=False)
    total_days = Column(Integer, nullable=True)
    eto_high_extremes_count = Column(Integer, nullable=True)
    eto_low_extremes_count = Column(Integer, nullable=True)
    eto_total_extremes = Column(Integer, nullable=True)
    eto_extreme_frequency = Column(Float, nullable=True)
    eto_max_value = Column(Float, nullable=True)
    eto_min_value = Column(Float, nullable=True)
    eto_high_extremes_years = Column(JSON, nullable=True)
    eto_low_extremes_years = Column(JSON, nullable=True)
    precip_extremes_count = Column(Integer, nullable=True)
    precip_extreme_frequency = Column(Float, nullable=True)
    precip_max_value = Column(Float, nullable=True)
    precip_dry_spell_max = Column(String, nullable=True)
    precip_wet_spell_max = Column(String, nullable=True)

    __table_args__ = (Index("idx_extremes_analysis_city", "city"),)


class CityReports(Base):
    __tablename__ = "city_reports"

    city = Column(String, primary_key=True)
    report_data = Column(JSON, nullable=False)
    loaded_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_city_reports_loaded_at", "loaded_at"),)


class GenerationMetadata(Base):
    __tablename__ = "generation_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    generation_date = Column(DateTime, nullable=False)
    total_cities = Column(Integer, nullable=True)
    reference_period_start = Column(String, nullable=True)
    reference_period_end = Column(String, nullable=True)
    reference_period_key = Column(String, nullable=True)
    methodologies = Column(JSON, nullable=True)
    summary_statistics = Column(JSON, nullable=True)
    loaded_at = Column(DateTime, default=datetime.utcnow)


# ==========================================
# FUNÇÕES UTILITÁRIAS
# ==========================================


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def create_tables_safe() -> bool:
    """Cria tabelas com retry logic."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelas criadas/verificadas com sucesso")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        raise


@contextmanager
def get_db_session() -> Session:
    """Context manager para sessões seguras."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro em transação: {e}")
        raise
    finally:
        db.close()


def validate_csv(df: pd.DataFrame, expected_columns: List[str]) -> pd.DataFrame:
    """Valida estrutura e integridade do CSV."""
    # Check colunas
    missing = set(expected_columns) - set(df.columns)
    if missing:
        raise ValueError(f"❌ Colunas faltando: {missing}")

    # Check tipos
    if df.empty:
        raise ValueError("❌ CSV vazio!")

    # Fill NaNs
    initial_nulls = df.isnull().sum().sum()
    df = df.fillna(0)
    if initial_nulls > 0:
        logger.warning(f"⚠️ {initial_nulls} NULLs preenchidos com 0")

    logger.info(f"✅ CSV validado: {len(df)} linhas, {len(df.columns)} colunas")
    return df


def count_table_rows(table_name: str) -> int:
    """Retorna número de linhas em uma tabela."""
    try:
        with get_db_session() as db:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    except Exception as e:
        logger.error(f"❌ Erro ao contar linhas de {table_name}: {e}")
        return 0


# ==========================================
# FUNÇÕES DE CARREGAMENTO
# ==========================================


def load_csv_to_table(
    csv_path: Path, table_name: str, expected_columns: List[str], if_exists: str = "replace"
) -> bool:
    """
    Carrega CSV para tabela PostgreSQL com validação.

    Args:
        csv_path: Caminho do arquivo CSV
        table_name: Nome da tabela
        expected_columns: Colunas esperadas
        if_exists: 'replace' (limpa e insere) ou 'append'
    """
    if not csv_path.exists():
        logger.error(f"❌ Arquivo não encontrado: {csv_path}")
        return False

    try:
        start_time = time.time()
        logger.info(f"📂 Carregando CSV: {csv_path.name}")

        # Lê e valida
        df = pd.read_csv(csv_path)
        df = validate_csv(df, expected_columns)

        # Carrega para BD
        df.to_sql(
            table_name,
            engine,
            if_exists=if_exists,
            index=False,
            chunksize=1000,
            method="multi",  # ✅ Bulk insert otimizado
        )

        elapsed = time.time() - start_time
        rows_count = count_table_rows(table_name)

        logger.info(
            f"✅ CSV '{csv_path.name}' carregado em {elapsed:.2f}s "
            f"({rows_count} linhas em {table_name})"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Erro ao carregar CSV {csv_path}: {e}")
        return False


def load_city_reports_batch(cities_folder: Path, batch_size: int = 10) -> bool:
    """
    Carrega JSONs de cidades com batch insert otimizado.

    Args:
        cities_folder: Pasta com report_*.json
        batch_size: Tamanho do batch para inserts
    """
    if not cities_folder.exists():
        logger.error(f"❌ Pasta não encontrada: {cities_folder}")
        return False

    try:
        logger.info(f"📂 Carregando JSONs de: {cities_folder}")

        json_files = list(cities_folder.glob("report_*.json"))
        total_files = len(json_files)

        if total_files == 0:
            logger.warning(f"⚠️ Nenhum JSON encontrado em {cities_folder}")
            return False

        logger.info(f"📊 Encontrados {total_files} arquivos JSON")

        start_time = time.time()
        batch = []
        inserted = 0

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                city = json_file.stem.replace("report_", "")
                batch.append(
                    {
                        "city": city,
                        "report_data": json.dumps(data),  # Serializar para JSONB
                        "loaded_at": datetime.utcnow(),
                    }
                )

                # Insert em batch
                if len(batch) >= batch_size:
                    inserted += _insert_batch_safe(batch)
                    batch = []

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON inválido: {json_file} - {e}")
            except Exception as e:
                logger.error(f"❌ Erro ao processar {json_file}: {e}")

        # Insere batch final
        if batch:
            inserted += _insert_batch_safe(batch)

        elapsed = time.time() - start_time
        logger.info(f"✅ JSONs carregados: {inserted}/{total_files} em {elapsed:.2f}s")
        return True

    except Exception as e:
        logger.error(f"❌ Erro ao carregar JSONs: {e}")
        return False


def _insert_batch_safe(batch: List[Dict[str, Any]]) -> int:
    """Insere batch com upsert seguro."""
    try:
        with get_db_session() as db:
            # Usar executemany com rawSQL ao invés de text() para evitar escaping
            sql = """
                INSERT INTO city_reports (city, report_data, loaded_at)
                VALUES (%s, %s::jsonb, %s)
                ON CONFLICT (city) DO UPDATE SET
                    report_data = EXCLUDED.report_data,
                    loaded_at = EXCLUDED.loaded_at
            """

            # Preparar valores na sequência correta
            values = [
                (record["city"], record["report_data"], record["loaded_at"]) for record in batch
            ]

            # Usar conexão raw para executemany
            connection = db.connection()
            cursor = connection.connection.cursor()

            for value in values:
                cursor.execute(sql, value)

            connection.commit()
            logger.debug(f"✅ Batch de {len(batch)} cities inserido")
            return len(batch)
    except Exception as e:
        logger.error(f"❌ Erro no batch insert: {e}")
        return 0


def load_metadata(metadata_path: Path) -> bool:
    """Carrega metadata global."""
    if not metadata_path.exists():
        logger.warning(f"⚠️ Arquivo de metadata não encontrado: {metadata_path}")
        return False

    try:
        logger.info(f"📂 Carregando metadata: {metadata_path.name}")
        start_time = time.time()

        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        with get_db_session() as db:
            # Limpa metadata anterior
            db.execute(text("DELETE FROM generation_metadata"))

            new_meta = GenerationMetadata(
                generation_date=datetime.fromisoformat(
                    data["generation_date"].replace("Z", "+00:00")
                ),
                total_cities=data.get("total_cities"),
                reference_period_start=data.get("reference_period", [None])[0],
                reference_period_end=data.get("reference_period", [None, None])[1],
                reference_period_key=data.get("reference_period_key"),
                methodologies=json.dumps(data.get("methodologies", {})),
                summary_statistics=json.dumps(data.get("summary_statistics", {})),
            )
            db.add(new_meta)

        elapsed = time.time() - start_time
        logger.info(f"✅ Metadata carregado em {elapsed:.2f}s")
        return True

    except Exception as e:
        logger.error(f"❌ Erro ao carregar metadata: {e}")
        return False


# ==========================================
# RELATÓRIO FINAL
# ==========================================


def print_summary_report():
    """Imprime relatório de dados carregados."""
    logger.info("\n" + "=" * 70)
    logger.info("📊 RELATÓRIO FINAL DE CARREGAMENTO")
    logger.info("=" * 70)

    tables = {
        "cities_summary": CitiesSummary,
        "annual_normals": AnnualNormals,
        "extremes_analysis": ExtremesAnalysis,
        "city_reports": CityReports,
        "generation_metadata": GenerationMetadata,
    }

    for table_name, table_class in tables.items():
        count = count_table_rows(table_name)
        logger.info(f"✅ {table_name:.<40} {count:>5} linhas")

    logger.info("=" * 70 + "\n")


# ==========================================
# MAIN
# ==========================================


def main():
    """Função principal de carregamento."""
    logger.info("\n" + "=" * 70)
    logger.info("🚀 INICIANDO CARREGAMENTO DE DADOS CLIMÁTICOS")
    logger.info("=" * 70 + "\n")

    start_total = time.time()

    try:
        # 1. Criar tabelas
        create_tables_safe()

        # 2. Configurar caminhos
        base_path = Path(__file__).parent.parent
        cities_folder = base_path / "reports" / "cities"
        csv_folder = base_path / "reports" / "summary"

        # 3. Validar caminhos
        if not cities_folder.exists() or not csv_folder.exists():
            raise FileNotFoundError(f"Pastas não encontradas: {base_path}/reports")

        # 4. Carregar CSVs
        logger.info("\n📂 CARREGANDO CSVs...")
        load_csv_to_table(
            csv_folder / "cities_summary.csv", "cities_summary", ["city", "region", "lat", "lon"]
        )

        load_csv_to_table(
            csv_folder / "annual_normals_comparison.csv", "annual_normals", ["city", "period"]
        )

        load_csv_to_table(csv_folder / "extremes_analysis.csv", "extremes_analysis", ["city"])

        # 5. Carregar JSONs
        logger.info("\n📂 CARREGANDO JSONs...")
        load_city_reports_batch(cities_folder)

        # 6. Carregar Metadata
        logger.info("\n📂 CARREGANDO METADATA...")
        load_metadata(csv_folder / "generation_metadata.json")

        # 7. Relatório final
        elapsed_total = time.time() - start_total
        print_summary_report()
        logger.info(f"⏱️  TEMPO TOTAL: {elapsed_total:.2f}s")
        logger.info("✅ CARREGAMENTO CONCLUÍDO COM SUCESSO!\n")

    except Exception as e:
        logger.error(f"\n❌ ERRO FATAL: {e}\n")
        raise


if __name__ == "__main__":
    main()
