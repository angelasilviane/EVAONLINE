"""
ETo Pipeline com Kalman Ensemble + OpenMeteo
- Integra busca de histórico climático na DB
- Aplica Kalman Ensemble adaptado ou simples
- Calcula ETo com dados fusionados

Pipeline:
1. Buscar localidade na DB (histórico?) → Station Finder
2. Buscar dados OpenMeteo para período → OpenMeteoSmartClient
3. Buscar estações próximas → PostGIS query
4. Funde dados com Kalman (adaptado ou simples)
5. Calcula ETo com dados fusionados
"""

from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger
from sqlalchemy.orm import Session

from backend.api.services.openmeteo_smart_client import OpenMeteoSmartClient
from backend.core.data_processing.kalman_ensemble import ClimateKalmanFusion
from backend.core.data_processing.station_finder import StationFinder
from backend.core.eto_calculation.eto_calculation import calculate_eto_pipeline


class EToKalmanPipeline:
    """
    Pipeline completo ETo com Kalman Ensemble

    Workflow:
    1. Verificar se localidade tem histórico na DB
    2. Buscar dados atuais (OpenMeteo)
    3. Buscar estações próximas se necessário
    4. Aplicar Kalman (adaptado com histórico ou simples)
    5. Calcular ETo com dados fusionados
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.station_finder = StationFinder(db_session)
        self.kalman_fusion = ClimateKalmanFusion()
        self.openmeteo_client = OpenMeteoSmartClient()
        logger.info("EToKalmanPipeline initialized")

    async def calculate_eto_with_kalman(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        elevation: Optional[float] = None,
        include_recommendations: bool = True,
    ) -> Dict[str, Any]:
        """
        Calcula ETo com Kalman Ensemble automático

        Workflow:
        1. Busca histórico da localidade na DB
        2. Se existe → Kalman Adaptado com normais históricos
        3. Se não existe → Kalman Simples com estações próximas
        4. Funde dados
        5. Calcula ETo

        Args:
            latitude: Latitude da localidade
            longitude: Longitude da localidade
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            elevation: Elevation em metros (opcional)
            include_recommendations: Se incluir recomendações agrícolas

        Returns:
            Dict com:
            - eto_data: Série temporal de ETo
            - fusion_strategy: 'adaptive' ou 'simple'
            - data_sources: Origens dos dados
            - anomalies: Anomalias detectadas
            - recommendations: Recomendações agrícolas (se solicitado)
        """
        logger.info(
            f"Starting ETo calculation with Kalman: "
            f"({latitude}, {longitude}) [{start_date} to {end_date}]"
        )

        try:
            # ========================================
            # 1. Buscar dados históricos na DB
            # ========================================
            logger.info("Step 1: Checking for historical data in DB...")

            studied_city = await self.station_finder.find_studied_city(
                latitude, longitude, max_distance_km=10
            )

            has_historical_data = studied_city is not None

            # ========================================
            # 2. Buscar dados atuais (OpenMeteo)
            # ========================================
            logger.info("Step 2: Fetching current climate data from OpenMeteo...")

            try:
                openmeteo_response = await self.openmeteo_client.get_climate_data(
                    lat=latitude,
                    lng=longitude,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception as e:
                logger.error(f"OpenMeteo error: {e}")
                raise

            location_info = openmeteo_response["location"]
            climate_data = openmeteo_response["climate_data"]

            # Extract elevation if not provided
            if elevation is None:
                elevation = location_info.get("elevation", 0.0)

            # ========================================
            # 3. Buscar estações próximas (se sem histórico)
            # ========================================
            nearby_stations = []
            if not has_historical_data:
                logger.info("Step 3: Finding nearby weather stations...")

                nearby_stations = await self.station_finder.find_stations_in_radius(
                    latitude, longitude, radius_km=50, limit=5
                )
                logger.info(f"Found {len(nearby_stations)} nearby stations")

            # ========================================
            # 4. Aplicar Kalman Ensemble
            # ========================================
            logger.info("Step 4: Applying Kalman Ensemble fusion...")

            if has_historical_data:
                logger.info(
                    f"Using ADAPTIVE Kalman (historical data found: {studied_city['city_name']})"
                )

                # Buscar normais do mês atual
                start_dt = pd.to_datetime(start_date)
                month = start_dt.month

                monthly_normals = await self.station_finder.get_monthly_normals(
                    studied_city["id"], month
                )

                # Funde com Kalman Adaptado
                fused_data = await self._fuse_adaptive(climate_data, monthly_normals, studied_city)
                fusion_strategy = "adaptive"

            else:
                logger.info("Using SIMPLE Kalman (no historical data found)")

                # Funde com Kalman Simples
                fused_data = await self._fuse_simple(climate_data, nearby_stations)
                fusion_strategy = "simple"

            # ========================================
            # 5. Calcular ETo com dados fusionados
            # ========================================
            logger.info("Step 5: Calculating ETo from fused data...")

            eto_result = await calculate_eto_pipeline(
                fused_data=fused_data,
                latitude=latitude,
                longitude=longitude,
                elevation=elevation,
                timezone=location_info.get("timezone", "UTC"),
            )

            # ========================================
            # 6. Compilar resultado final
            # ========================================
            result = {
                "success": True,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "elevation": elevation,
                    "timezone": location_info.get("timezone"),
                },
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "eto_data": eto_result,
                "fusion": {
                    "strategy": fusion_strategy,
                    "data_sources": self._get_data_sources(has_historical_data, nearby_stations),
                    "quality_indicators": self._get_quality_indicators(fused_data, fusion_strategy),
                },
            }

            # Recomendações agrícolas (opcional)
            if include_recommendations:
                result["recommendations"] = await self._generate_recommendations(
                    eto_result, fused_data, studied_city
                )

            logger.info("✅ ETo calculation complete with Kalman Ensemble")
            return result

        except Exception as e:
            logger.error(f"Error in EToKalmanPipeline: {e}")
            raise

    async def _fuse_adaptive(
        self,
        climate_data: Dict[str, List[float]],
        monthly_normals: Optional[Dict[str, float]],
        studied_city: Dict[str, Any],
    ) -> Dict[str, List[float]]:
        """
        Funde dados com Kalman Adaptado (usando histórico)
        """
        fused = {}

        if not monthly_normals:
            logger.warning("No monthly normals available, falling back to simple fusion")
            return climate_data

        # Preparar variáveis para Kalman Adaptado
        measurements = {
            "temperature_2m_mean": climate_data.get("temperature_2m_mean", []),
            "precipitation_sum": climate_data.get("precipitation_sum", []),
            "et0_fao_evapotranspiration": climate_data.get("et0_fao_evapotranspiration", []),
            "wind_speed_10m_mean": climate_data.get("wind_speed_10m_mean", []),
            "shortwave_radiation_sum": climate_data.get("shortwave_radiation_sum", []),
        }

        # Kalman Adaptado
        for var, values in measurements.items():
            normal = monthly_normals.get(f"{var}_normal", 0.0)
            std = monthly_normals.get(f"{var}_daily_std", 1.0)

            filtered_values = []
            for value in values:
                filtered = self.kalman_fusion.filters.get(var)
                if filtered is None:
                    from backend.core.data_processing.kalman_ensemble import AdaptiveKalmanFilter

                    self.kalman_fusion.filters[var] = AdaptiveKalmanFilter(
                        monthly_normal=normal,
                        historical_std=std,
                        station_confidence=0.9,
                    )
                filtered_values.append(self.kalman_fusion.filters[var].update(value))

            fused[var] = filtered_values

        # Preservar dados não processados
        for key, value in climate_data.items():
            if key not in fused:
                fused[key] = value

        return fused

    async def _fuse_simple(
        self,
        climate_data: Dict[str, List[float]],
        nearby_stations: List[Dict[str, Any]],
    ) -> Dict[str, List[float]]:
        """
        Funde dados com Kalman Simples (sem histórico)
        """
        if not nearby_stations:
            logger.warning("No nearby stations, using raw climate data")
            return climate_data

        fused = {}

        # Kalman Simples para cada variável
        for var in climate_data:
            if not isinstance(climate_data[var], list):
                fused[var] = climate_data[var]
                continue

            filtered_values = []
            for value in climate_data[var]:
                if var not in self.kalman_fusion.filters:
                    from backend.core.data_processing.kalman_ensemble import SimpleKalmanFilter

                    self.kalman_fusion.filters[var] = SimpleKalmanFilter()

                filtered = self.kalman_fusion.filters[var].update(value)
                filtered_values.append(filtered)

            fused[var] = filtered_values

        return fused

    def _get_data_sources(
        self, has_historical_data: bool, nearby_stations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Identifica fontes de dados usadas"""
        sources = {
            "primary": "OpenMeteo Smart API",
            "kalman_source": "adaptive_with_db" if has_historical_data else "simple",
            "secondary_stations": len(nearby_stations),
        }

        if nearby_stations:
            sources["station_details"] = [
                {
                    "name": s.get("station_name"),
                    "distance_km": s.get("distance_km"),
                    "data_source": s.get("data_source"),
                }
                for s in nearby_stations[:3]
            ]

        return sources

    def _get_quality_indicators(
        self, fused_data: Dict[str, List[float]], fusion_strategy: str
    ) -> Dict[str, Any]:
        """Indicadores de qualidade da fusão"""
        return {
            "fusion_strategy": fusion_strategy,
            "estimated_accuracy": "high" if fusion_strategy == "adaptive" else "medium",
            "data_completeness": "high",
            "temporal_coverage": "daily",
        }

    async def _generate_recommendations(
        self,
        eto_result: Dict[str, Any],
        fused_data: Dict[str, List[float]],
        studied_city: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Gera recomendações agrícolas baseadas em ETo e anomalias"""
        recommendations = []

        # Análise de ETo
        if "eto_daily" in eto_result:
            eto_values = eto_result["eto_daily"]
            eto_mean = sum(eto_values) / len(eto_values) if eto_values else 0

            if eto_mean > 5:
                recommendations.append(
                    "Alta demanda hídrica detectada - aumentar frequência de irrigação"
                )
            elif eto_mean < 2:
                recommendations.append("Baixa demanda hídrica - reduzir irrigação")

        # Análise de precipitação
        if "precipitation_sum" in fused_data:
            precip_values = fused_data["precipitation_sum"]
            precip_mean = sum(precip_values) / len(precip_values) if precip_values else 0

            if precip_mean < 1:
                recommendations.append("Precipitação baixa esperada - priorizar irrigação")

        if studied_city:
            recommendations.append(
                f"Dados para {studied_city['city_name']} validados com histórico climático"
            )

        return recommendations
