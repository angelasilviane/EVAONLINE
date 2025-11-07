"""
Test script para nws_forecast_client.py - Dados reais da API NWS.
"""

import asyncio
from datetime import datetime

from nws_forecast_client import NWSForecastClient


async def test_nws_forecast():
    """Testa cliente NWS com dados reais."""

    # Coordenadas de teste (Denver, CO - dentro da cobertura NWS)
    lat = 39.7392
    lon = -104.9903

    print("=" * 80)
    print("TESTE: NWS Forecast Client - Dados Reais")
    print("=" * 80)
    print(f"Coordenadas: lat={lat}, lon={lon} (Denver, CO)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    async with NWSForecastClient() as client:
        # Teste 1: Verificar cobertura
        print("1. Verificando cobertura...")
        in_coverage = client.is_in_coverage(lat, lon)
        print(f"   ✓ Coordenadas na cobertura: {in_coverage}")
        print()

        # Teste 2: Health check
        print("2. Health check da API...")
        try:
            health = await client.health_check()
            print(f"   ✓ Status: {health['status']}")
            print(f"   ✓ Base URL: {health['base_url']}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
        print()

        # Teste 3: Dados horários
        print("3. Obtendo dados HORARIOS...")
        try:
            hourly_data = await client.get_forecast_data(lat, lon)
            print(f"   ✓ Total de períodos: {len(hourly_data)}")

            if hourly_data:
                first = hourly_data[0]
                print(f"   ✓ Primeiro período:")
                print(f"      - Timestamp: {first.timestamp}")
                print(
                    f"      - Temp: {first.temp_celsius:.1f}°C"
                    if first.temp_celsius
                    else "      - Temp: N/A"
                )
                print(
                    f"      - Umidade: {first.humidity_percent:.1f}%"
                    if first.humidity_percent
                    else "      - Umidade: N/A"
                )
                print(
                    f"      - Vento: {first.wind_speed_ms:.1f} m/s"
                    if first.wind_speed_ms
                    else "      - Vento: N/A"
                )
                print(
                    f"      - Precip: {first.precip_mm:.1f} mm"
                    if first.precip_mm
                    else "      - Precip: N/A"
                )
                print(f"      - Previsão: {first.short_forecast}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            import traceback

            traceback.print_exc()
        print()

        # Teste 4: Dados diários (agregados)
        print("4. Obtendo dados DIARIOS (agregados - limit 5 days)...")
        try:
            daily_data = await client.get_daily_forecast_data(lat, lon)
            print(f"   ✓ Total de dias: {len(daily_data)}")
            print()

            for i, day in enumerate(daily_data, 1):
                print(f"   Dia {i}: {day.date.date()}")
                print(
                    f"      - Temp média: {day.temp_mean_celsius:.1f}°C"
                    if day.temp_mean_celsius
                    else "      - Temp média: N/A"
                )
                print(
                    f"      - Temp máx: {day.temp_max_celsius:.1f}°C"
                    if day.temp_max_celsius
                    else "      - Temp máx: N/A"
                )
                print(
                    f"      - Temp mín: {day.temp_min_celsius:.1f}°C"
                    if day.temp_min_celsius
                    else "      - Temp mín: N/A"
                )
                print(
                    f"      - Umidade: {day.humidity_mean_percent:.1f}%"
                    if day.humidity_mean_percent
                    else "      - Umidade: N/A"
                )
                print(
                    f"      - Vento: {day.wind_speed_mean_ms:.1f} m/s"
                    if day.wind_speed_mean_ms
                    else "      - Vento: N/A"
                )
                print(
                    f"      - Precip total: {day.precip_total_mm:.1f} mm"
                    if day.precip_total_mm
                    else "      - Precip total: N/A"
                )
                print(
                    f"      - Prob precip: {day.probability_precip_mean_percent:.1f}%"
                    if day.probability_precip_mean_percent
                    else "      - Prob precip: N/A"
                )
                print(f"      - Períodos horários: {len(day.hourly_data)}")
                print(f"      - Previsão: {day.short_forecast}")
                print()
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            import traceback

            traceback.print_exc()
        print()

        # Teste 5: Atribuição
        print("5. Informações de atribuição...")
        attribution = client.get_attribution()
        print(f"   ✓ Fonte: {attribution['source']}")
        print(f"   ✓ Licença: {attribution['license']}")
        print(f"   ✓ Terms: {attribution['terms_url']}")
        print()

        # Teste 6: Disponibilidade
        print("6. Informações de disponibilidade...")
        availability = client.get_data_availability_info()
        print(f"   ✓ Região: {availability['coverage']['region']}")
        print(f"   ✓ Bbox: {availability['coverage']['bbox']}")
        print(
            f"   ✓ Horizonte: {availability['forecast_horizon']['days']} dias / {availability['forecast_horizon']['hours']} horas"
        )
        print(f"   ✓ Atualização: {availability['update_frequency']}")
        print()

    print("=" * 80)
    print("TESTE CONCLUÍDO!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_nws_forecast())
