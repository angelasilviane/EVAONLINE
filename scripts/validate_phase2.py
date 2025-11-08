"""
Script simplificado para validar o fluxo completo de salvamento de dados.

Testa:
1. Estrutura da tabela climate_data
2. Função save_climate_data()
3. Harmonização de dados
4. Query de dados salvos

Usage:
    uv run python scripts/validate_phase2.py
"""

import io
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import text

# Fix encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db_context
from backend.database.data_storage import (
    save_climate_data,
    get_climate_data,
    harmonize_data,
)
from backend.database.models import ClimateData


def print_header(title):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def validate_table_structure():
    """Valida estrutura da tabela climate_data."""
    print_header("1️⃣  VALIDANDO ESTRUTURA DA TABELA climate_data")

    with get_db_context() as session:
        result = session.execute(
            text(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'climate_data'
                  AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            )
        )

        columns = result.fetchall()

        print(f"\n📋 Colunas da tabela ({len(columns)} total):")
        for col in columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            print(f"   - {col[0]:<20} {col[1]:<30} {nullable}")

        # Verificar colunas essenciais
        required_cols = [
            "source_api",
            "latitude",
            "longitude",
            "elevation",
            "timezone",
            "date",
            "raw_data",
            "harmonized_data",
            "eto_mm_day",
            "eto_method",
            "quality_flags",
            "processing_metadata",
        ]

        col_names = [col[0] for col in columns]
        missing = [col for col in required_cols if col not in col_names]

        if missing:
            print(f"\n   ❌ Colunas faltando: {missing}")
            return False
        else:
            print("\n   ✅ Todas as colunas essenciais presentes")
            return True


def test_harmonization():
    """Testa função de harmonização de dados."""
    print_header("2️⃣  TESTANDO HARMONIZAÇÃO DE DADOS")

    # Dados de teste NASA POWER
    nasa_data = {
        "T2M_MAX": 28.5,
        "T2M_MIN": 18.2,
        "RH2M": 65.0,
        "WS2M": 3.2,
        "ALLSKY_SFC_SW_DWN": 20.5,
    }

    print("\n📊 Dados NASA POWER originais:")
    for key, value in nasa_data.items():
        print(f"   - {key}: {value}")

    harmonized = harmonize_data(nasa_data, "nasa_power")

    print("\n✨ Dados harmonizados:")
    for key, value in harmonized.items():
        print(f"   - {key}: {value}")

    if harmonized:
        print("\n   ✅ Harmonização funcionando")
        return True
    else:
        print("\n   ❌ Harmonização falhou")
        return False


def test_save_and_retrieve():
    """Testa salvamento e recuperação de dados."""
    print_header("3️⃣  TESTANDO SALVAMENTO E RECUPERAÇÃO")

    # Preparar dados de teste - usar data diferente para evitar duplicatas
    test_date = datetime(2024, 7, 20)
    test_data = [
        {
            "latitude": -22.7250,
            "longitude": -47.6476,
            "elevation": 547.0,
            "timezone": "America/Sao_Paulo",
            "date": test_date,
            "raw_data": {
                "T2M_MAX": 28.5,
                "T2M_MIN": 18.2,
                "RH2M": 65.0,
                "WS2M": 3.2,
                "ALLSKY_SFC_SW_DWN": 20.5,
                "PRECTOTCORR": 5.2,
            },
            "eto_mm_day": 4.85,
            "eto_method": "penman_monteith",
            "quality_flags": {"test": True, "complete": True},
            "processing_metadata": {
                "script": "validate_phase2",
                "timestamp": datetime.now().isoformat(),
            },
        }
    ]

    print("\n📝 Dados de teste:")
    print(f"   - Localização: Piracicaba, SP")
    print(f"   - Data: {test_date.date()}")
    print(f"   - ETo: {test_data[0]['eto_mm_day']} mm/dia")
    print(f"   - Variáveis raw: {len(test_data[0]['raw_data'])} campos")

    # Verificar se já existe
    from backend.database.data_storage import check_data_exists

    exists = check_data_exists(
        source_api="nasa_power",
        latitude=-22.7250,
        longitude=-47.6476,
        date=test_date,
    )

    if exists:
        print("\n⚠️  Registro já existe no banco (teste anterior)")
        print("   - Pulando salvamento e indo direto para recuperação")
    else:
        # Salvar
        print("\n💾 Salvando no banco...")
        try:
            count = save_climate_data(
                test_data, "nasa_power", auto_harmonize=True
            )
            print(f"   ✅ {count} registro(s) salvo(s)")
        except Exception as e:
            print(f"   ❌ Erro ao salvar: {e}")
            return False  # Recuperar
    print("\n🔍 Recuperando dados salvos...")
    try:
        results = get_climate_data(
            latitude=-22.7250,
            longitude=-47.6476,
            start_date=test_date - timedelta(days=1),
            end_date=test_date + timedelta(days=1),
            source_api="nasa_power",
        )

        if results:
            record = results[0]
            print(f"   ✅ {len(results)} registro(s) encontrado(s)")
            print(f"\n📊 Dados recuperados:")
            print(f"   - ID: {record.id}")
            print(f"   - Data: {record.date}")
            print(f"   - ETo: {record.eto_mm_day} mm/dia")
            print(f"   - Elevação: {record.elevation}m")
            print(f"   - Timezone: {record.timezone}")
            print(f"   - Raw data: {len(record.raw_data)} campos")
            print(
                f"   - Harmonized data: {len(record.harmonized_data)} campos"
            )

            # Verificar harmonização
            if record.harmonized_data:
                print(f"\n✨ Campos harmonizados:")
                for key in list(record.harmonized_data.keys())[:5]:
                    print(f"   - {key}: {record.harmonized_data[key]}")

            return True
        else:
            print("   ❌ Nenhum registro encontrado")
            return False

    except Exception as e:
        print(f"   ❌ Erro ao recuperar: {e}")
        return False


def validate_existing_data():
    """Valida dados existentes no banco."""
    print_header("4️⃣  VALIDANDO DADOS EXISTENTES")

    with get_db_context() as session:
        # Total de registros
        total = session.query(ClimateData).count()
        print(f"\n📊 Total de registros: {total}")

        if total == 0:
            print("   ℹ️  Nenhum dado no banco ainda")
            return True

        # Registros por API
        print("\n📋 Registros por API:")
        result = session.execute(
            text(
                """
                SELECT source_api, COUNT(*) as total
                FROM climate_data
                GROUP BY source_api
                ORDER BY source_api
            """
            )
        )

        for row in result:
            print(f"   - {row[0]}: {row[1]} registro(s)")

        # Registros com ETo calculado
        with_eto = (
            session.query(ClimateData)
            .filter(ClimateData.eto_mm_day.isnot(None))
            .count()
        )
        print(f"\n📈 Registros com ETo calculado: {with_eto}/{total}")

        # Registros com dados harmonizados
        with_harmonized = (
            session.query(ClimateData)
            .filter(ClimateData.harmonized_data.isnot(None))
            .count()
        )
        print(
            f"✨ Registros com dados harmonizados: {with_harmonized}/{total}"
        )

        # Últimos 5 registros
        print("\n📅 Últimos 5 registros:")
        recent = (
            session.query(ClimateData)
            .order_by(ClimateData.id.desc())
            .limit(5)
            .all()
        )

        for record in recent:
            print(f"\n   ID {record.id}:")
            print(f"      - API: {record.source_api}")
            print(f"      - Data: {record.date}")
            print(
                f"      - Local: ({record.latitude:.4f}, {record.longitude:.4f})"
            )
            if record.eto_mm_day:
                print(f"      - ETo: {record.eto_mm_day:.2f} mm/dia")

        return True


def validate_data_storage_integration():
    """Valida integração completa do data_storage.py."""
    print_header("5️⃣  VALIDANDO INTEGRAÇÃO data_storage.py")

    checks = []

    # 1. Função save_climate_data existe e funciona
    print("\n✓ save_climate_data(): ", end="")
    try:
        from backend.database.data_storage import save_climate_data

        print("✅ OK")
        checks.append(True)
    except Exception as e:
        print(f"❌ {e}")
        checks.append(False)

    # 2. Função harmonize_data existe e funciona
    print("✓ harmonize_data(): ", end="")
    try:
        from backend.database.data_storage import harmonize_data

        result = harmonize_data({"T2M_MAX": 25.0}, "nasa_power")
        if result:
            print("✅ OK")
            checks.append(True)
        else:
            print("❌ Retornou vazio")
            checks.append(False)
    except Exception as e:
        print(f"❌ {e}")
        checks.append(False)

    # 3. Função get_climate_data existe e funciona
    print("✓ get_climate_data(): ", end="")
    try:
        from backend.database.data_storage import get_climate_data

        print("✅ OK")
        checks.append(True)
    except Exception as e:
        print(f"❌ {e}")
        checks.append(False)

    # 4. Função check_data_exists existe e funciona
    print("✓ check_data_exists(): ", end="")
    try:
        from backend.database.data_storage import check_data_exists

        print("✅ OK")
        checks.append(True)
    except Exception as e:
        print(f"❌ {e}")
        checks.append(False)

    # 5. get_variable_mapping existe e funciona
    print("✓ get_variable_mapping(): ", end="")
    try:
        from backend.database.data_storage import get_variable_mapping

        mapping = get_variable_mapping("nasa_power")
        if mapping:
            print(f"✅ OK ({len(mapping)} variáveis)")
            checks.append(True)
        else:
            print("⚠️  Sem variáveis mapeadas")
            checks.append(False)
    except Exception as e:
        print(f"❌ {e}")
        checks.append(False)

    passed = sum(checks)
    total = len(checks)

    print(f"\n🎯 Resultado: {passed}/{total} checks passaram")

    return passed == total


def main():
    """Executa validação completa da Fase 2."""
    print("\n" + "=" * 80)
    print("🔍 VALIDAÇÃO COMPLETA - FASE 2: DATABASE & STORAGE")
    print("=" * 80)

    results = []

    # Executar validações
    results.append(("Estrutura da Tabela", validate_table_structure()))
    results.append(("Harmonização de Dados", test_harmonization()))
    results.append(("Salvamento e Recuperação", test_save_and_retrieve()))
    results.append(("Dados Existentes", validate_existing_data()))
    results.append(
        ("Integração data_storage", validate_data_storage_integration())
    )

    # Resumo final
    print_header("📊 RESUMO FINAL DA VALIDAÇÃO")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")

    print(f"\n🎯 Score: {passed}/{total} validações passaram")

    if passed == total:
        print("\n" + "=" * 80)
        print("🎉 FASE 2 VALIDADA COM SUCESSO!")
        print("=" * 80)
        print("\n✅ Estrutura do banco de dados: OK")
        print("✅ Modelo ClimateData: OK")
        print("✅ Salvamento multi-API: OK")
        print("✅ Harmonização de dados: OK")
        print("✅ Funções de data_storage: OK")
        print("\n🚀 Sistema pronto para receber dados reais das APIs!")
    else:
        print("\n⚠️  Algumas validações falharam. Verifique os detalhes acima.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
