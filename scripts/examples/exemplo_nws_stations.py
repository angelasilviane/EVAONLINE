"""
Exemplo de uso dos novos métodos de dados de estações NWS.

Este exemplo demonstra como:
1. Buscar estações meteorológicas próximas a uma coordenada
2. Obter observações históricas de uma estação específica
"""

import asyncio
import os
import sys

from backend.api.services.nws_hourly_forecast_client import NWSClient

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def exemplo_nws_stations():
    """Exemplo completo de uso dos métodos de estações NWS."""

    # Cria cliente NWS
    client = NWSClient()

    try:
        # Coordenadas de exemplo (São Paulo, Brasil -
        # mas fora da cobertura USA)
        # Vamos usar Washington DC como exemplo
        lat, lon = 38.8977, -77.0365

        print("🌤️ Exemplo: Dados de estações NWS")
        print(f"📍 Coordenadas: {lat}, {lon}")
        print()

        # 1. Busca estações próximas (até 50km, máximo 10 estações)
        print("🔍 Buscando estações próximas...")
        stations = await client.get_nearby_stations(lat=lat, lon=lon, max_distance_km=50, limit=10)

        print(f"✅ Encontradas {len(stations)} estações:")
        for i, station in enumerate(stations, 1):
            print(f"  {i}. {station.station_id}: {station.name}")
            print(f"     Provedor: {station.provider}")
        print()

        if stations:
            # 2. Obtém observações da estação mais próxima
            station = stations[0]
            print(f"📊 Obtendo observações da estação {station.station_id}...")

            observations = await client.get_station_observations(
                station_id=station.station_id,
                limit=10,  # Últimas 10 observações
            )

            print(f"✅ {len(observations)} observações encontradas:")
            print("   Timestamp              Temp(°C)  Umid(%)  Vento(m/s)")
            print("   --------------------  --------  -------  ----------")

            for obs in observations[:5]:  # Mostra apenas 5 mais recentes
                timestamp = obs.timestamp[:19]  # Remove timezone
                temp = f"{obs.temp_celsius:>8.1f}" if obs.temp_celsius else "     N/A"
                humidity = f"{obs.humidity_percent:>7.0f}" if obs.humidity_percent else "    N/A"
                wind = f"{obs.wind_speed_ms:>10.1f}" if obs.wind_speed_ms else "       N/A"

                print(f"   {timestamp}  {temp}  {humidity}  {wind}")

            print()
            print("💡 Dica: As observações incluem temperatura, umidade,")
            print("         velocidade do vento, pressão, visibilidade, etc.")

    except Exception as e:
        print(f"❌ Erro: {e}")

    finally:
        # Sempre fechar o cliente
        await client.close()


if __name__ == "__main__":
    asyncio.run(exemplo_nws_stations())
if __name__ == "__main__":
    asyncio.run(exemplo_nws_stations())
