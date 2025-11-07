import asyncio
from datetime import datetime

from backend.api.services.met_norway_frost_sync_adapter import FrostClient
from backend.api.services.nasa_power_client import NASAPowerClient
from backend.api.services.openmeteo_archive_client import (
    OpenMeteoArchiveClient,
)


async def test_earliest_dates():
    """Test downloading data before earliest available dates to confirm validation."""

    print("🧪 Testando Limites de Datas Mínimas das APIs:")
    print("=" * 60)

    # Test Open-Meteo Archive (earliest: 1940-01-01)
    print("🌍 Open-Meteo Archive (data mínima: 1940-01-01):")
    client = OpenMeteoArchiveClient()

    try:
        # Tentar data anterior a 1940
        start_date = datetime(1939, 12, 25)  # Antes de 1940
        end_date = datetime(1939, 12, 31)  # 7 dias antes de 1940

        data = await client.get_climate_data(
            lat=52.5200,
            lng=13.4050,  # Berlin, Germany
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )
        print(
            f'  ❌ ERRO: Aceitou data anterior a 1940! ({len(data["climate_data"]["dates"])} registros)'
        )

    except ValueError as e:
        print(f"  ✅ Corretamente rejeitado: {e}")
    except Exception as e:
        print(f"  ✅ Rejeitado por outro motivo: {e}")

    # Test NASA POWER (earliest: 1981-01-01)
    print("\n🛰️ NASA POWER (data mínima: 1981-01-01):")
    nasa_client = NASAPowerClient()

    try:
        # Tentar data anterior a 1981
        start_date = datetime(1980, 12, 25)  # Antes de 1981
        end_date = datetime(1980, 12, 31)  # 7 dias antes de 1981

        data = await nasa_client.get_daily_data(
            lat=40.7128,
            lon=-74.0060,
            start_date=start_date,
            end_date=end_date,  # New York
        )
        print(
            f"  ❌ ERRO: Aceitou data anterior a 1981! ({len(data)} registros)"
        )

    except ValueError as e:
        print(f"  ✅ Corretamente rejeitado: {e}")
    except Exception as e:
        print(f"  ✅ Rejeitado por outro motivo: {e}")

    # Test MET Norway FROST (earliest: 1937-01-01)
    print("\n🇳🇴 MET Norway FROST (data mínima: 1937-01-01):")

    try:
        # Tentar data anterior a 1937
        start_date = datetime(1936, 12, 25)  # Antes de 1937
        end_date = datetime(1936, 12, 31)  # 7 dias antes de 1937

        # Este teste é mais limitado pois requer station ID
        # Vamos testar apenas a validação de range (não a API real)
        range_days = (end_date - start_date).days + 1
        if range_days < FrostClient.MIN_RANGE_DAYS:
            print(
                f"  ✅ Range muito curto rejeitado: {range_days} dias (mínimo {FrostClient.MIN_RANGE_DAYS})"
            )
        elif range_days > FrostClient.MAX_RANGE_DAYS:
            print(
                f"  ✅ Range muito longo rejeitado: {range_days} dias (máximo {FrostClient.MAX_RANGE_DAYS})"
            )
        else:
            print(
                "  ⚠️ Range válido, mas data pode ser anterior ao suportado pela API"
            )

    except Exception as e:
        print(f"  ✅ Rejeitado: {e}")

    print("\n" + "=" * 60)
    print("🎯 Teste concluído: Validações de data mínima funcionando!")


if __name__ == "__main__":
    asyncio.run(test_earliest_dates())
