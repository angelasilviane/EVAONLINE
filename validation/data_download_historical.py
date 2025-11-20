"""
Historical Data Download for Validation (1990-2024)
Fusão multi-fonte com Kalman Ensemble + referência climática
Versão corrigida, otimizada e robusta – 2025
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from loguru import logger

# Imports específicos da sua stack de validação (sem DB/Redis/Celery)
from validation_logic_eto.api.services.nasa_power.nasa_power_sync_adapter import (
    NASAPowerSyncAdapter,
)
from validation_logic_eto.api.services.openmeteo_archive.openmeteo_archive_sync_adapter import (
    OpenMeteoArchiveSyncAdapter,
)
from validation_logic_eto.core.data_processing.data_preprocessing import (
    preprocessing,
)
from validation_logic_eto.core.data_processing.kalman_ensemble import (
    ClimateKalmanEnsemble,
)


async def download_historical_weather_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    use_fusion: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Baixa e funde dados históricos (1990–2024) usando NASA POWER + OpenMeteo Archive
    com fusão adaptativa via Kalman Ensemble + referência climática local.

    Retorna DataFrame limpo e fundido, pronto para cálculo de ETo.
    """
    warnings_list: List[str] = []

    logger.info(
        f"Iniciando download histórico: {start_date} → {end_date} | "
        f"({latitude:.4f}, {longitude:.4f}) | Fusão: {'ON' if use_fusion else 'OFF'}"
    )

    # Validação básica
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError(f"Coordenadas inválidas: ({latitude}, {longitude})")

    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    if start_dt < pd.to_datetime("1990-01-01"):
        raise ValueError("Período anterior a 1990-01-01 não suportado")

    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")

    preprocessed_sources: List[pd.DataFrame] = []

    # ========================================================
    # 1. NASA POWER (opcional, só se use_fusion=True)
    # ========================================================
    if use_fusion:
        try:
            logger.debug("Baixando NASA POWER...")
            nasa_adapter = NASAPowerSyncAdapter()

            # Usar asyncio.to_thread para evitar conflito de event loop
            nasa_raw = await asyncio.to_thread(
                nasa_adapter.get_daily_data_sync,
                lat=latitude,
                lon=longitude,
                start_date=start_dt,
                end_date=end_dt,
            )

            if nasa_raw:
                records = []
                for r in nasa_raw:
                    records.append(
                        {
                            "date": pd.to_datetime(r.date),
                            "T2M_MAX": r.temp_max,
                            "T2M_MIN": r.temp_min,
                            "T2M": r.temp_mean,
                            "RH2M": r.humidity,
                            "WS2M": r.wind_speed,
                            "ALLSKY_SFC_SW_DWN": r.solar_radiation,
                            "PRECTOTCORR": r.precipitation,
                        }
                    )

                df_nasa = pd.DataFrame(records).set_index("date")
                df_nasa = df_nasa.replace(-999.0, np.nan)

                # Salvar dados RAW do NASA POWER
                Path("temp").mkdir(exist_ok=True)
                df_nasa.to_csv(
                    f"temp/nasa_power_raw_{start_dt.year}_{latitude:.4f}_{longitude:.4f}.csv"
                )
                logger.info(f"💾 NASA POWER RAW salvo: {len(df_nasa)} dias")

                df_clean, warn = preprocessing(
                    df_nasa, latitude=latitude, region="global"
                )
                preprocessed_sources.append(df_clean)
                warnings_list.extend(warn)

                # Salvar dados PREPROCESSED do NASA POWER
                df_clean.to_csv(
                    f"temp/nasa_power_preprocessed_{start_dt.year}_{latitude:.4f}_{longitude:.4f}.csv"
                )
                logger.info(
                    f"💾 NASA POWER PREPROCESSED salvo: {len(df_clean)} dias"
                )

                logger.success(f"NASA POWER → {len(df_clean)} dias válidos")
            else:
                warnings_list.append("NASA POWER: sem dados retornados")
                logger.warning("NASA POWER retornou vazio")

        except Exception as e:
            warnings_list.append(f"NASA POWER erro: {e}")
            logger.warning(f"Erro NASA POWER: {e}")

    # ========================================================
    # 2. OpenMeteo Archive (obrigatório)
    # ========================================================
    try:
        logger.debug("Baixando OpenMeteo Archive...")
        om_adapter = OpenMeteoArchiveSyncAdapter()
        om_raw = await asyncio.to_thread(
            om_adapter.get_daily_data_sync,
            lat=latitude,
            lon=longitude,
            start_date=start_str,
            end_date=end_str,
        )

        if not om_raw:
            raise ValueError("OpenMeteo Archive retornou vazio")

        df_om = pd.DataFrame(om_raw)
        df_om["date"] = pd.to_datetime(df_om["date"])
        df_om = df_om.set_index("date")

        # Salvar dados RAW do OpenMeteo Archive
        df_om.to_csv(
            f"temp/openmeteo_archive_raw_{start_dt.year}_{latitude:.4f}_{longitude:.4f}.csv"
        )
        logger.info(f"💾 OpenMeteo Archive RAW salvo: {len(df_om)} dias")

        # Harmonização de nomes
        rename_map = {
            "temperature_2m_max": "T2M_MAX",
            "temperature_2m_min": "T2M_MIN",
            "temperature_2m_mean": "T2M",
            "relative_humidity_2m_mean": "RH2M",
            "wind_speed_10m_mean": "WS2M",
            "shortwave_radiation_sum": "ALLSKY_SFC_SW_DWN",
            "precipitation_sum": "PRECTOTCORR",
        }
        df_om = df_om.rename(columns=rename_map)
        df_om = df_om.replace(-999.0, np.nan)

        # Remove colunas desnecessárias
        drop_cols = {
            "et0_fao_evapotranspiration",
            "relative_humidity_2m_max",
            "relative_humidity_2m_min",
        }
        df_om = df_om.drop(
            columns=[c for c in drop_cols if c in df_om.columns],
            errors="ignore",
        )

        df_clean_om, warn_om = preprocessing(
            df_om, latitude=latitude, region="global"
        )
        preprocessed_sources.append(df_clean_om)
        warnings_list.extend(warn_om)

        # Salvar dados PREPROCESSED do OpenMeteo Archive
        df_clean_om.to_csv(
            f"temp/openmeteo_archive_preprocessed_{start_dt.year}_{latitude:.4f}_{longitude:.4f}.csv"
        )
        logger.info(
            f"💾 OpenMeteo Archive PREPROCESSED salvo: {len(df_clean_om)} dias"
        )

        logger.success(f"OpenMeteo Archive → {len(df_clean_om)} dias válidos")

    except Exception as e:
        logger.error(f"OpenMeteo Archive falhou: {e}")
        if not preprocessed_sources:
            raise RuntimeError("Nenhuma fonte retornou dados válidos") from e
        warnings_list.append(f"OpenMeteo Archive erro crítico: {e}")

    if not preprocessed_sources:
        raise RuntimeError(
            "Nenhuma fonte forneceu dados após pré-processamento"
        )

    # ========================================================
    # 3. FUSÃO KALMAN (se tiver ≥2 fontes e use_fusion=True)
    # ========================================================
    final_df: pd.DataFrame

    if use_fusion and len(preprocessed_sources) > 1:
        logger.info(
            f"Aplicando Kalman Ensemble em {len(preprocessed_sources)} fontes..."
        )

        kalman = ClimateKalmanEnsemble()
        fused_records = []

        all_dates = pd.date_range(start_dt, end_dt, freq="D")

        for current_date in all_dates:
            measurements: dict[str, float] = {}

            for idx, df_src in enumerate(preprocessed_sources):
                if current_date not in df_src.index:
                    continue
                row = df_src.loc[current_date]

                # Adiciona medições com sufixo de índice para o Kalman identificar múltiplas fontes
                # Formato: T2M_MAX0, T2M_MAX1, etc.
                for var in [
                    "T2M_MAX",
                    "T2M_MIN",
                    "T2M",
                    "RH2M",
                    "WS2M",
                    "ALLSKY_SFC_SW_DWN",
                    "PRECTOTCORR",
                ]:
                    # row é uma Series, então usamos try/except para acessar
                    try:
                        val = row[var]
                        # Garante que é escalar e não NaN
                        if not pd.isna(val):
                            key = f"{var}{idx}" if idx > 0 else var
                            measurements[key] = float(val)
                    except (KeyError, IndexError, TypeError):
                        continue

            if not measurements:
                continue

            try:
                fused_day = kalman.auto_fuse_sync(
                    latitude=latitude,
                    longitude=longitude,
                    measurements=measurements,
                    date=current_date,  # importante: passa a referência climática correta (mês)
                )

                fused_vals = fused_day["fused"]
                fused_records.append(
                    {
                        "date": current_date,
                        "T2M_MAX": fused_vals.get("T2M_MAX"),
                        "T2M_MIN": fused_vals.get("T2M_MIN"),
                        "T2M": fused_vals.get("T2M"),
                        "RH2M": fused_vals.get("RH2M"),
                        "WS2M": fused_vals.get("WS2M"),
                        "ALLSKY_SFC_SW_DWN": fused_vals.get(
                            "ALLSKY_SFC_SW_DWN"
                        ),
                        "PRECTOTCORR": fused_vals.get("PRECTOTCORR"),
                    }
                )

            except Exception as e_k:
                logger.debug(f"Kalman falhou em {current_date}: {e_k}")
                # Fallback: média simples
                row_dict = {"date": current_date}
                for var in [
                    "T2M_MAX",
                    "T2M_MIN",
                    "T2M",
                    "RH2M",
                    "WS2M",
                    "ALLSKY_SFC_SW_DWN",
                    "PRECTOTCORR",
                ]:
                    vals = [
                        df_src.loc[current_date, var]
                        for df_src in preprocessed_sources
                        if current_date in df_src.index
                        and var in df_src.columns
                        and pd.notna(df_src.loc[current_date, var])
                    ]
                    row_dict[var] = np.nanmean(vals) if vals else np.nan
                fused_records.append(row_dict)

        if fused_records:
            final_df = pd.DataFrame(fused_records).set_index("date")

            # Salvar dados FUSED do Kalman
            final_df.to_csv(
                f"temp/kalman_fused_{start_dt.year}_{latitude:.4f}_{longitude:.4f}.csv"
            )
            logger.info(f"💾 KALMAN FUSED salvo: {len(final_df)} dias")

            logger.success(f"Fusão Kalman concluída → {len(final_df)} dias")
        else:
            logger.warning("Nenhum dia fundido → usando primeira fonte")
            final_df = preprocessed_sources[0]

    else:
        # Sem fusão ou apenas 1 fonte → usa OpenMeteo pré-processado
        final_df = preprocessed_sources[-1]  # preferência OpenMeteo
        logger.info("Fusão desativada → usando única fonte disponível")

    # ========================================================
    # 4. CHECAGEM FINAL DE QUALIDADE
    # ========================================================
    expected_days = (end_dt - start_dt).days + 1
    actual_days = len(final_df)

    if actual_days < expected_days * 0.9:
        warnings_list.append(
            f"Cobertura baixa: {actual_days}/{expected_days} dias ({actual_days/expected_days:.1%})"
        )

    missing_pct = final_df.isna().mean() * 100
    for var, pct in missing_pct.items():
        if pct > 20:
            warnings_list.append(f"{var}: {pct:.1f}% dados faltando")

    # Salva para debug (opcional, mas muito útil)
    Path("temp").mkdir(exist_ok=True)
    final_df.to_csv(
        f"temp/historical_final_{start_dt.year}_{latitude}_{longitude}.csv"
    )

    logger.success(
        f"Download concluído → {actual_days} dias | {len(warnings_list)} aviso(s)"
    )
    return final_df, warnings_list


# Wrapper síncrono (para quem chama de código sync)
def download_historical_weather_data_sync(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    use_fusion: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """Versão síncrona – segura em qualquer contexto"""
    import asyncio

    return asyncio.run(
        download_historical_weather_data(
            latitude, longitude, start_date, end_date, use_fusion
        )
    )
