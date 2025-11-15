import asyncio
from datetime import datetime, timedelta

from backend.api.services.met_norway_client import (
    METNorwayClient,
)
from backend.api.services.nws_forecast_client import NWSClient
from backend.api.services.openmeteo_forecast_client import (
    OpenMeteoForecastClient,
)


async def test_forecast_limits():
    """Test forecast limits for each climate source."""

    print("🧪 Testando Limites de Forecast das APIs:")
    print("=" * 60)

    today = datetime.now().date()

    # Test Open-Meteo Forecast Limits (max 16 days future)
    print("🌍 Open-Meteo Forecast (máximo: +16 dias):")

    client = OpenMeteoForecastClient()

    # Test within limits (+10 days future)
    try:
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=10)

        data = await client.get_climate_data(
            lat=52.5200,
            lng=13.4050,  # Berlin
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )
        print(
            f'  ✅ Dentro do limite (+10 dias): {len(data["climate_data"]["dates"])} registros'
        )

    except Exception as e:
        print(f"  ❌ Dentro do limite falhou: {e}")

    # Test beyond limits (+20 days future - should fail)
    try:
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=20)  # Beyond 16 day limit

        data = await client.get_climate_data(
            lat=52.5200,
            lng=13.4050,  # Berlin
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )
        print(
            f'  ❌ ERRO: Aceitou além do limite (+20 dias)! {len(data["climate_data"]["dates"])} registros'
        )

    except Exception as e:
        print(f"  ✅ Corretamente rejeitado (+20 dias): {str(e)[:100]}...")

    # Test NWS Forecast Limits (max 7 days future)
    print("\n🇺🇸 NWS Forecast (máximo: +7 dias):")

    nws_client = NWSClient()

    # Test within limits (+5 days future)
    try:
        data = await nws_client.get_forecast_data(
            lat=40.7128, lon=-74.0060  # New York - corrected parameter
        )
        print(f"  ✅ Dentro do limite: {len(data)} registros de forecast")

    except Exception as e:
        print(f"  ❌ Dentro do limite falhou: {e}")

    # Test MET Norway Locationforecast Limits (max 14 days future)
    print("\n🇳🇴 MET Norway Locationforecast (máximo: +14 dias):")

    met_client = METNorwayClient()

    # Test within limits (+10 days future)
    try:
        data = await met_client.get_daily_forecast(
            lat=59.9139, lon=10.7522  # Oslo - corrected method name
        )
        print(f"  ✅ Dentro do limite: {len(data)} registros de forecast")

    except Exception as e:
        print(f"  ❌ Dentro do limite falhou: {e}")

    print("\n" + "=" * 60)
    print("🎯 Teste de limites de forecast concluído!")


if __name__ == "__main__":
    asyncio.run(test_forecast_limits())
