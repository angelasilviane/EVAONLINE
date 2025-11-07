"""
Test script for NWS Forecast Sync Adapter

Testa o adapter sincrono que wraps o cliente assincrono.
"""

from datetime import datetime, timedelta

from loguru import logger

from nws_forecast_sync_adapter import NWSDailyForecastSyncAdapter


def main():
    """Executar testes do NWS Forecast Sync Adapter."""
    logger.info("=" * 70)
    logger.info("TESTE: NWS Forecast Sync Adapter")
    logger.info("=" * 70)

    # Criar adapter
    adapter = NWSDailyForecastSyncAdapter()

    # Coordenadas de teste: Denver, CO
    lat = 39.7392
    lon = -104.9903
    location_name = "Denver, CO"

    logger.info(f"\n📍 Localização: {location_name}")
    logger.info(f"   Coordenadas: {lat}°N, {lon}°W")

    # 1. Health Check
    logger.info("\n" + "=" * 70)
    logger.info("1. HEALTH CHECK")
    logger.info("=" * 70)

    try:
        is_healthy = adapter.health_check_sync()
        if is_healthy:
            logger.success("✅ NWS API está acessível")
        else:
            logger.error("❌ NWS API não está acessível")
            return
    except Exception as e:
        logger.error(f"❌ Health check falhou: {e}")
        return

    # 2. Get Attribution
    logger.info("\n" + "=" * 70)
    logger.info("2. ATTRIBUTION")
    logger.info("=" * 70)

    try:
        attribution = adapter.get_attribution()
        logger.info(f"📄 {attribution}")
    except Exception as e:
        logger.error(f"❌ Erro ao obter atribuição: {e}")

    # 3. Get Daily Data (próximos 5 dias)
    logger.info("\n" + "=" * 70)
    logger.info("3. DADOS DIÁRIOS (Próximos 5 dias)")
    logger.info("=" * 70)

    try:
        # Período: hoje até daqui a 5 dias
        start_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = start_date + timedelta(days=5)

        logger.info(f"📅 Período: {start_date.date()} a {end_date.date()}")

        daily_data = adapter.get_daily_data_sync(
            lat, lon, start_date, end_date
        )

        if not daily_data:
            logger.warning("⚠️  Nenhum dado retornado")
            return

        logger.success(f"✅ Recuperados {len(daily_data)} dias de dados")

        # Mostrar dados
        logger.info("\n" + "-" * 70)
        logger.info("PREVISÃO DIÁRIA:")
        logger.info("-" * 70)

        for i, record in enumerate(daily_data, 1):
            logger.info(f"\n📅 Dia {i}: {record.date}")
            logger.info(f"   🌡️  Temperatura:")
            if record.temp_max is not None:
                logger.info(f"      Máxima: {record.temp_max:.1f}°C")
            if record.temp_mean is not None:
                logger.info(f"      Média:  {record.temp_mean:.1f}°C")
            if record.temp_min is not None:
                logger.info(f"      Mínima: {record.temp_min:.1f}°C")

            if record.humidity_mean is not None:
                logger.info(
                    f"   💧 Umidade média: {record.humidity_mean:.1f}%"
                )

            if record.wind_speed_mean is not None:
                logger.info(
                    f"   💨 Vento médio: {record.wind_speed_mean:.1f} m/s"
                )
            if record.wind_speed_max is not None:
                logger.info(
                    f"   💨 Vento máximo: {record.wind_speed_max:.1f} m/s"
                )

            if record.precipitation_sum is not None:
                logger.info(
                    f"   🌧️  Precipitação: {record.precipitation_sum:.1f} mm"
                )

        # Estatísticas gerais
        logger.info("\n" + "=" * 70)
        logger.info("ESTATÍSTICAS GERAIS")
        logger.info("=" * 70)

        temps_max = [r.temp_max for r in daily_data if r.temp_max is not None]
        temps_min = [r.temp_min for r in daily_data if r.temp_min is not None]
        temps_mean = [
            r.temp_mean for r in daily_data if r.temp_mean is not None
        ]
        humidities = [
            r.humidity_mean for r in daily_data if r.humidity_mean is not None
        ]
        winds_mean = [
            r.wind_speed_mean
            for r in daily_data
            if r.wind_speed_mean is not None
        ]
        precips = [
            r.precipitation_sum
            for r in daily_data
            if r.precipitation_sum is not None
        ]

        if temps_max:
            logger.info(
                f"🌡️  Temp máxima: {max(temps_max):.1f}°C (max), {min(temps_max):.1f}°C (min)"
            )
        if temps_min:
            logger.info(
                f"🌡️  Temp mínima: {max(temps_min):.1f}°C (max), {min(temps_min):.1f}°C (min)"
            )
        if temps_mean:
            avg_temp = sum(temps_mean) / len(temps_mean)
            logger.info(f"🌡️  Temp média: {avg_temp:.1f}°C (período)")
        if humidities:
            avg_humidity = sum(humidities) / len(humidities)
            logger.info(f"💧 Umidade média: {avg_humidity:.1f}% (período)")
        if winds_mean:
            avg_wind = sum(winds_mean) / len(winds_mean)
            logger.info(f"💨 Vento médio: {avg_wind:.1f} m/s (período)")
        if precips:
            total_precip = sum(precips)
            logger.info(f"🌧️  Precipitação total: {total_precip:.1f} mm")

    except ValueError as e:
        logger.error(f"❌ Erro de validação: {e}")
    except Exception as e:
        logger.error(f"❌ Erro ao obter dados: {e}")
        import traceback

        traceback.print_exc()

    # 4. Teste com período passado (deve retornar vazio ou filtrado)
    logger.info("\n" + "=" * 70)
    logger.info("4. TESTE PERÍODO PASSADO")
    logger.info("=" * 70)

    try:
        past_start = datetime.now() - timedelta(days=10)
        past_end = datetime.now() - timedelta(days=5)

        logger.info(
            f"📅 Período passado: {past_start.date()} a {past_end.date()}"
        )

        past_data = adapter.get_daily_data_sync(lat, lon, past_start, past_end)

        if not past_data:
            logger.info(
                "✅ Nenhum dado (esperado - NWS só tem forecast futuro)"
            )
        else:
            logger.warning(f"⚠️  {len(past_data)} dias retornados (inesperado)")

    except Exception as e:
        logger.error(f"❌ Erro no teste de período passado: {e}")

    logger.info("\n" + "=" * 70)
    logger.info("✅ TESTES COMPLETOS")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
