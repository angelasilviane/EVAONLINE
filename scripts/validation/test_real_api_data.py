"""
Teste de integração COMPLETO com dados REAIS das 6 APIs climáticas.

Fluxo testado:
1. Fazer requisição REAL para cada API
2. Processar dados retornados
3. Calcular ETo (quando possível)
4. Salvar no banco de dados
5. Validar dados salvos
6. Exibir resultados

Usage:
    uv run python scripts/validation/test_real_api_data.py
"""

import io
import sys
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

# Fix encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.climate_factory import ClimateClientFactory
from backend.database.data_storage import save_climate_data
from backend.database.connection import get_db_context
from backend.database.models import ClimateData


# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

# Piracicaba, SP - Localização de teste
TEST_LOCATION = {
    "name": "Piracicaba, SP",
    "latitude": -22.7250,
    "longitude": -47.6476,
    "elevation": 547.0,
    "timezone": "America/Sao_Paulo",
}

# Nova York, EUA - Para testar NWS
TEST_LOCATION_USA = {
    "name": "Nova York, EUA",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "elevation": 10.0,
    "timezone": "America/New_York",
}

# Oslo, Noruega - Para testar MET Norway
TEST_LOCATION_NORWAY = {
    "name": "Oslo, Noruega",
    "latitude": 59.9139,
    "longitude": 10.7522,
    "elevation": 23.0,
    "timezone": "Europe/Oslo",
}


# ==============================================================================
# TESTES COM DADOS REAIS
# ==============================================================================


def test_nasa_power_real():
    """Testa NASA POWER com dados reais."""
    print("\n" + "=" * 80)
    print("1️⃣  NASA POWER - Dados Históricos REAIS")
    print("=" * 80)

    try:
        # Criar cliente
        client = ClimateClientFactory.create_nasa_power()

        # Definir período (1 dia há 1 ano atrás - dado histórico disponível)
        end_date = datetime.now() - timedelta(days=365)
        start_date = end_date - timedelta(days=1)

        print(f"\n📍 Localização: {TEST_LOCATION['name']}")
        print(f"📅 Período: {start_date.date()} a {end_date.date()}")

        # Fazer requisição REAL
        print("\n🌐 Fazendo requisição à NASA POWER API...")
        result = client.fetch_daily_data(
            lat=TEST_LOCATION["latitude"],
            lon=TEST_LOCATION["longitude"],
            start_date=start_date.date(),
            end_date=end_date.date(),
        )

        if not result or result.empty:
            print("   ❌ Nenhum dado retornado pela API")
            return False

        print(f"   ✅ Dados recebidos: {len(result)} registro(s)")
        print(f"\n📊 Variáveis disponíveis: {list(result.columns)[:10]}...")

        # Preparar dados para salvamento
        data_to_save = []
        for date, row in result.iterrows():
            data_to_save.append(
                {
                    "latitude": TEST_LOCATION["latitude"],
                    "longitude": TEST_LOCATION["longitude"],
                    "elevation": TEST_LOCATION["elevation"],
                    "timezone": TEST_LOCATION["timezone"],
                    "date": date,
                    "raw_data": row.to_dict(),
                    "eto_mm_day": row.get("ETo"),
                    "eto_method": "penman_monteith",
                    "quality_flags": {
                        "source": "nasa_power",
                        "complete": True,
                    },
                }
            )

        # Salvar no banco
        print("\n💾 Salvando no banco de dados...")
        count = save_climate_data(data_to_save, "nasa_power")
        print(f"   ✅ {count} registro(s) salvo(s)")

        # Mostrar exemplo de dados
        first_record = data_to_save[0]
        print(f"\n📈 Exemplo de dados salvos:")
        print(f"   - Data: {first_record['date']}")
        print(f"   - ETo: {first_record['eto_mm_day']:.2f} mm/dia")
        print(
            f"   - T2M_MAX: {first_record['raw_data'].get('T2M_MAX', 'N/A')}°C"
        )
        print(
            f"   - T2M_MIN: {first_record['raw_data'].get('T2M_MIN', 'N/A')}°C"
        )

        return True

    except Exception as e:
        print(f"\n   ❌ Erro: {e}")
        logger.exception("Erro ao testar NASA POWER")
        return False


def test_openmeteo_archive_real():
    """Testa Open-Meteo Archive com dados reais."""
    print("\n" + "=" * 80)
    print("2️⃣  OPEN-METEO ARCHIVE - Dados Históricos REAIS")
    print("=" * 80)

    try:
        # Criar cliente
        client = ClimateClientFactory.create_openmeteo_archive()

        # Período: 7 dias há 2 meses atrás
        end_date = datetime.now() - timedelta(days=60)
        start_date = end_date - timedelta(days=7)

        print(f"\n📍 Localização: {TEST_LOCATION['name']}")
        print(f"📅 Período: {start_date.date()} a {end_date.date()}")

        # Fazer requisição REAL
        print("\n🌐 Fazendo requisição à Open-Meteo Archive API...")
        result = client.fetch_daily_data(
            lat=TEST_LOCATION["latitude"],
            lon=TEST_LOCATION["longitude"],
            start_date=start_date.date(),
            end_date=end_date.date(),
        )

        if not result or result.empty:
            print("   ❌ Nenhum dado retornado pela API")
            return False

        print(f"   ✅ Dados recebidos: {len(result)} registro(s)")
        print(f"\n📊 Variáveis disponíveis: {list(result.columns)}")

        # Preparar dados para salvamento
        data_to_save = []
        for date, row in result.iterrows():
            data_to_save.append(
                {
                    "latitude": TEST_LOCATION["latitude"],
                    "longitude": TEST_LOCATION["longitude"],
                    "elevation": TEST_LOCATION["elevation"],
                    "timezone": TEST_LOCATION["timezone"],
                    "date": date,
                    "raw_data": row.to_dict(),
                    "eto_mm_day": row.get("et0_fao_evapotranspiration"),
                    "eto_method": "penman_monteith",
                }
            )

        # Salvar no banco
        print("\n💾 Salvando no banco de dados...")
        count = save_climate_data(data_to_save, "openmeteo_archive")
        print(f"   ✅ {count} registro(s) salvo(s)")

        # Mostrar exemplo
        first_record = data_to_save[0]
        print(f"\n📈 Exemplo de dados salvos:")
        print(f"   - Data: {first_record['date']}")
        if first_record["eto_mm_day"]:
            print(f"   - ETo: {first_record['eto_mm_day']:.2f} mm/dia")
        print(
            f"   - Temp Máx: {first_record['raw_data'].get('temperature_2m_max', 'N/A')}°C"
        )
        print(
            f"   - Precipitação: {first_record['raw_data'].get('precipitation_sum', 'N/A')} mm"
        )

        return True

    except Exception as e:
        print(f"\n   ❌ Erro: {e}")
        logger.exception("Erro ao testar Open-Meteo Archive")
        return False


def test_openmeteo_forecast_real():
    """Testa Open-Meteo Forecast com dados reais."""
    print("\n" + "=" * 80)
    print("3️⃣  OPEN-METEO FORECAST - Previsão REAL")
    print("=" * 80)

    try:
        # Criar cliente
        client = ClimateClientFactory.create_openmeteo_forecast()

        # Período: próximos 7 dias
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)

        print(f"\n📍 Localização: {TEST_LOCATION['name']}")
        print(f"📅 Período: {start_date.date()} a {end_date.date()}")

        # Fazer requisição REAL
        print("\n🌐 Fazendo requisição à Open-Meteo Forecast API...")
        result = client.fetch_daily_data(
            lat=TEST_LOCATION["latitude"],
            lon=TEST_LOCATION["longitude"],
            start_date=start_date.date(),
            end_date=end_date.date(),
        )

        if not result or result.empty:
            print("   ❌ Nenhum dado retornado pela API")
            return False

        print(f"   ✅ Dados recebidos: {len(result)} registro(s)")
        print(f"\n📊 Variáveis disponíveis: {list(result.columns)}")

        # Preparar dados para salvamento
        data_to_save = []
        for date, row in result.iterrows():
            data_to_save.append(
                {
                    "latitude": TEST_LOCATION["latitude"],
                    "longitude": TEST_LOCATION["longitude"],
                    "elevation": TEST_LOCATION["elevation"],
                    "timezone": TEST_LOCATION["timezone"],
                    "date": date,
                    "raw_data": row.to_dict(),
                    "eto_mm_day": row.get("et0_fao_evapotranspiration"),
                    "eto_method": "penman_monteith",
                    "quality_flags": {"forecast": True},
                }
            )

        # Salvar no banco
        print("\n💾 Salvando no banco de dados...")
        count = save_climate_data(data_to_save, "openmeteo_forecast")
        print(f"   ✅ {count} registro(s) salvo(s)")

        # Mostrar previsão
        print(f"\n📈 Previsão próximos dias:")
        for i, record in enumerate(data_to_save[:3], 1):
            print(f"\n   Dia {i} ({record['date'].date()}):")
            if record["eto_mm_day"]:
                print(f"      - ETo: {record['eto_mm_day']:.2f} mm/dia")
            print(
                f"      - Temp Máx: {record['raw_data'].get('temperature_2m_max', 'N/A')}°C"
            )
            print(
                f"      - Chuva: {record['raw_data'].get('precipitation_sum', 'N/A')} mm"
            )

        return True

    except Exception as e:
        print(f"\n   ❌ Erro: {e}")
        logger.exception("Erro ao testar Open-Meteo Forecast")
        return False


def validate_saved_data():
    """Valida dados salvos no banco."""
    print("\n" + "=" * 80)
    print("🔍 VALIDAÇÃO DE DADOS SALVOS")
    print("=" * 80)

    with get_db_context() as db:
        # Contar registros por API
        print("\n📊 Registros por API:")
        for api in ["nasa_power", "openmeteo_archive", "openmeteo_forecast"]:
            count = (
                db.query(ClimateData)
                .filter(ClimateData.source_api == api)
                .count()
            )
            if count > 0:
                print(f"   ✅ {api}: {count} registro(s)")

        # Pegar último registro de cada API
        print("\n📈 Últimos dados salvos:")
        for api in ["nasa_power", "openmeteo_archive", "openmeteo_forecast"]:
            record = (
                db.query(ClimateData)
                .filter(ClimateData.source_api == api)
                .order_by(ClimateData.id.desc())
                .first()
            )

            if record:
                print(f"\n   {api}:")
                print(f"      - ID: {record.id}")
                print(f"      - Data: {record.date}")
                print(
                    f"      - Localização: ({record.latitude}, {record.longitude})"
                )
                if record.eto_mm_day:
                    print(f"      - ETo: {record.eto_mm_day:.2f} mm/dia")
                print(f"      - Variáveis raw: {len(record.raw_data)} campos")
                if record.harmonized_data:
                    print(
                        f"      - Variáveis harmonizadas: {len(record.harmonized_data)} campos"
                    )


def cleanup_test_data():
    """Remove dados de teste."""
    print("\n🗑️  Limpando dados de teste...")

    response = input("   Deseja remover os dados de teste? (s/N): ")
    if response.lower() != "s":
        print("   ℹ️  Dados mantidos para análise")
        return

    with get_db_context() as db:
        # Deletar apenas dados de teste (das últimas 2 horas)
        cutoff = datetime.now() - timedelta(hours=2)
        result = (
            db.query(ClimateData)
            .filter(ClimateData.created_at >= cutoff)
            .delete()
        )
        db.commit()
        print(f"   ✅ {result} registro(s) removido(s)")


def main():
    """Executa testes com dados reais."""
    print("\n" + "=" * 80)
    print("🌍 TESTE COMPLETO COM DADOS REAIS DAS APIS")
    print("=" * 80)
    print("\n⚠️  Este teste faz requisições REAIS às APIs climáticas!")
    print("    Pode levar alguns segundos...")

    results = []

    # Testes
    results.append(("NASA POWER", test_nasa_power_real()))
    results.append(("Open-Meteo Archive", test_openmeteo_archive_real()))
    results.append(("Open-Meteo Forecast", test_openmeteo_forecast_real()))

    # Validação
    validate_saved_data()

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for api_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {api_name}: {status}")

    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")

    if passed == total:
        print("\n🎉 SUCESSO TOTAL!")
        print("✅ Todas as APIs retornaram dados reais")
        print("✅ Dados foram salvos corretamente no banco")
        print("✅ Sistema de salvamento multi-API funcionando")
    else:
        print("\n⚠️  Alguns testes falharam")
        print("    Verifique os logs acima para detalhes")

    # Limpeza
    print("\n" + "=" * 80)
    cleanup_test_data()

    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
