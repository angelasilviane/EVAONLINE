"""
Test NWS Stations Client - Denver, Colorado
Comparação com dados reais de estações meteorológicas.

Localização: Denver, CO (39.7392°N, -104.9903°W)
Período: Hoje + 1 dia histórico (últimas 24h)
"""

import asyncio
from datetime import datetime, timedelta

import pandas as pd
from loguru import logger

from nws_stations_client import create_nws_stations_client


async def test_denver_stations():
    """
    Testa NWS Stations Client com Denver, Colorado.

    Busca:
    1. Estações próximas a Denver
    2. Observações das últimas 24 horas
    3. Agregação para dados diários
    4. Comparação de qualidade dos dados
    """
    logger.info("\n" + "=" * 70)
    logger.info("🏔️  NWS STATIONS - DENVER, COLORADO TEST")
    logger.info("=" * 70)

    # Coordenadas Denver (mesmas usadas no forecast test)
    lat, lon = 39.7392, -104.9903
    logger.info(f"📍 Location: Denver, CO ({lat}, {lon})")

    client = create_nws_stations_client()

    try:
        # ============================================================
        # 1. BUSCAR ESTAÇÕES PRÓXIMAS
        # ============================================================
        logger.info("\n" + "-" * 70)
        logger.info("1️⃣  SEARCHING NEARBY STATIONS")
        logger.info("-" * 70)

        stations = await client.find_nearest_stations(lat, lon, limit=5)

        logger.info(f"\n📊 Found {len(stations)} stations near Denver:")
        for i, station in enumerate(stations, 1):
            logger.info(f"\n  {i}. {station.name}")
            logger.info(f"     ID: {station.station_id}")
            logger.info(
                f"     Location: ({station.latitude:.4f}, {station.longitude:.4f})"
            )
            logger.info(f"     Elevation: {station.elevation_m}m")
            logger.info(f"     Timezone: {station.timezone}")

        if not stations:
            logger.error("❌ No stations found!")
            return

        # Usar primeira estação (mais próxima)
        main_station = stations[0]
        logger.info(
            f"\n✅ Selected station: {main_station.station_id} - {main_station.name}"
        )

        # ============================================================
        # 2. BUSCAR OBSERVAÇÕES (ÚLTIMAS 24H)
        # ============================================================
        logger.info("\n" + "-" * 70)
        logger.info("2️⃣  FETCHING OBSERVATIONS (LAST 24H)")
        logger.info("-" * 70)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)

        logger.info(f"📅 Period: {start_date.date()} to {end_date.date()}")
        logger.info(
            f"🕐 Time: {start_date.strftime('%H:%M')} to {end_date.strftime('%H:%M')} UTC"
        )

        observations = await client.get_station_observations(
            station_id=main_station.station_id,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(f"\n📊 Retrieved {len(observations)} hourly observations")

        if not observations:
            logger.warning("⚠️  No observations available!")
            return

        # ============================================================
        # 3. ANÁLISE DE QUALIDADE DOS DADOS
        # ============================================================
        logger.info("\n" + "-" * 70)
        logger.info("3️⃣  DATA QUALITY ANALYSIS")
        logger.info("-" * 70)

        # Contar valores não-nulos
        temps = [
            o.temp_celsius for o in observations if o.temp_celsius is not None
        ]
        humids = [
            o.humidity_percent
            for o in observations
            if o.humidity_percent is not None
        ]
        winds = [
            o.wind_speed_ms
            for o in observations
            if o.wind_speed_ms is not None
        ]
        pressures = [
            o.pressure_hpa for o in observations if o.pressure_hpa is not None
        ]
        precips = [
            o.precipitation_1h_mm
            for o in observations
            if o.precipitation_1h_mm is not None
        ]

        total = len(observations)
        logger.info(f"\n📈 Data Completeness:")
        logger.info(
            f"   Temperature:     {len(temps)}/{total} ({len(temps)/total*100:.1f}%)"
        )
        logger.info(
            f"   Humidity:        {len(humids)}/{total} ({len(humids)/total*100:.1f}%)"
        )
        logger.info(
            f"   Wind Speed:      {len(winds)}/{total} ({len(winds)/total*100:.1f}%)"
        )
        logger.info(
            f"   Pressure:        {len(pressures)}/{total} ({len(pressures)/total*100:.1f}%)"
        )
        logger.info(
            f"   Precipitation:   {len(precips)}/{total} ({len(precips)/total*100:.1f}%)"
        )

        # Contar observações atrasadas
        delayed_count = sum(1 for o in observations if o.is_delayed)
        logger.info(
            f"\n⏱️  Delayed Observations: {delayed_count}/{total} ({delayed_count/total*100:.1f}%)"
        )

        # ============================================================
        # 4. ESTATÍSTICAS HORÁRIAS
        # ============================================================
        logger.info("\n" + "-" * 70)
        logger.info("4️⃣  HOURLY STATISTICS")
        logger.info("-" * 70)

        if temps:
            logger.info(f"\n🌡️  Temperature:")
            logger.info(f"   Min:  {min(temps):.1f}°C")
            logger.info(f"   Max:  {max(temps):.1f}°C")
            logger.info(f"   Mean: {sum(temps)/len(temps):.1f}°C")

        if humids:
            logger.info(f"\n💧 Humidity:")
            logger.info(f"   Min:  {min(humids):.1f}%")
            logger.info(f"   Max:  {max(humids):.1f}%")
            logger.info(f"   Mean: {sum(humids)/len(humids):.1f}%")

        if winds:
            logger.info(f"\n💨 Wind Speed:")
            logger.info(f"   Min:  {min(winds):.1f} m/s")
            logger.info(f"   Max:  {max(winds):.1f} m/s")
            logger.info(f"   Mean: {sum(winds)/len(winds):.1f} m/s")

        if pressures:
            logger.info(f"\n🌐 Pressure:")
            logger.info(f"   Min:  {min(pressures):.1f} hPa")
            logger.info(f"   Max:  {max(pressures):.1f} hPa")
            logger.info(f"   Mean: {sum(pressures)/len(pressures):.1f} hPa")

        if precips:
            total_precip = sum(precips)
            logger.info(f"\n🌧️  Precipitation:")
            logger.info(f"   Total (24h): {total_precip:.1f} mm")
            logger.info(f"   Max (1h):    {max(precips):.1f} mm")

        # ============================================================
        # 5. AGREGAÇÃO PARA DADOS DIÁRIOS
        # ============================================================
        logger.info("\n" + "-" * 70)
        logger.info("5️⃣  DAILY AGGREGATION")
        logger.info("-" * 70)

        # Converter para DataFrame pandas
        df_data = []
        for obs in observations:
            df_data.append(
                {
                    "timestamp": obs.timestamp,
                    "temp_celsius": obs.temp_celsius,
                    "humidity_percent": obs.humidity_percent,
                    "wind_speed_ms": obs.wind_speed_ms,
                    "pressure_hpa": obs.pressure_hpa,
                    "precipitation_1h_mm": obs.precipitation_1h_mm or 0.0,
                }
            )

        df = pd.DataFrame(df_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        # Agregar para diário
        daily = (
            df.resample("D")
            .agg(
                {
                    "temp_celsius": "mean",
                    "humidity_percent": "mean",
                    "wind_speed_ms": "mean",
                    "pressure_hpa": "mean",
                    "precipitation_1h_mm": "sum",
                }
            )
            .round(2)
        )

        logger.info(f"\n📊 Daily Aggregated Data:")
        logger.info(f"\n{daily.to_string()}")

        # ============================================================
        # 6. MOSTRAR ÚLTIMAS 10 OBSERVAÇÕES
        # ============================================================
        logger.info("\n" + "-" * 70)
        logger.info("6️⃣  LATEST 10 OBSERVATIONS")
        logger.info("-" * 70)

        for i, obs in enumerate(observations[:10], 1):
            logger.info(f"\n  {i}. {obs.timestamp}")
            logger.info(f"     Temp:    {obs.temp_celsius}°C")
            logger.info(f"     Humidity: {obs.humidity_percent}%")
            logger.info(f"     Wind:    {obs.wind_speed_ms} m/s")
            logger.info(f"     Pressure: {obs.pressure_hpa} hPa")
            logger.info(f"     Precip:  {obs.precipitation_1h_mm} mm")
            logger.info(f"     Delayed: {obs.is_delayed}")

        # ============================================================
        # 7. OBSERVAÇÃO MAIS RECENTE
        # ============================================================
        logger.info("\n" + "-" * 70)
        logger.info("7️⃣  LATEST OBSERVATION (API ENDPOINT)")
        logger.info("-" * 70)

        latest = await client.get_latest_observation(main_station.station_id)

        if latest:
            logger.info(f"\n📡 Latest observation from API:")
            logger.info(f"   Timestamp:   {latest.timestamp}")
            logger.info(f"   Temperature: {latest.temp_celsius}°C")
            logger.info(f"   Humidity:    {latest.humidity_percent}%")
            logger.info(f"   Wind Speed:  {latest.wind_speed_ms} m/s")
            logger.info(f"   Pressure:    {latest.pressure_hpa} hPa")
            logger.info(f"   Precip (1h): {latest.precipitation_1h_mm} mm")
            logger.info(f"   Is Delayed:  {latest.is_delayed}")

            # Calcular delay atual
            now = datetime.utcnow()
            if latest.timestamp.tzinfo:
                from datetime import timezone

                now = now.replace(tzinfo=timezone.utc)
            delay = (now - latest.timestamp).total_seconds() / 60
            logger.info(f"   Current Delay: {delay:.1f} minutes")

        # ============================================================
        # RESUMO FINAL
        # ============================================================
        logger.info("\n" + "=" * 70)
        logger.info("📋 TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(
            f"✅ Station: {main_station.station_id} - {main_station.name}"
        )
        logger.info(f"✅ Location: Denver, CO ({lat}, {lon})")
        logger.info(f"✅ Observations: {len(observations)} (24h)")
        logger.info(
            f"✅ Data Quality: Temperature {len(temps)/total*100:.0f}%, Humidity {len(humids)/total*100:.0f}%"
        )
        logger.info(
            f"✅ Delayed Obs: {delayed_count}/{total} ({delayed_count/total*100:.1f}%)"
        )

        if temps:
            logger.info(
                f"✅ Temperature Range: {min(temps):.1f}°C to {max(temps):.1f}°C"
            )
        if precips:
            logger.info(f"✅ Total Precipitation: {sum(precips):.1f} mm")

        logger.info("=" * 70)
        logger.info("🎉 TEST COMPLETED SUCCESSFULLY!")

    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
        raise

    finally:
        await client.close()


if __name__ == "__main__":
    # Executar teste
    asyncio.run(test_denver_stations())
