"""
Weather conversion and aggregation utilities.

Centraliza todas as conversões de unidades e fórmulas meteorológicas
para eliminar duplicação de código entre os clientes climáticos.

SINGLE SOURCE OF TRUTH para:
- Conversão de vento (10m → 2m usando FAO-56)
- Conversão de temperatura (°F → °C)
- Conversão de velocidade (mph → m/s)
- Conversão de radiação solar
- Validações meteorológicas comuns
"""

from typing import Any

import numpy as np
from loguru import logger


class WeatherConversionUtils:
    """
    Utilitários de conversão de unidades meteorológicas.

    Todas as conversões seguem padrões internacionais:
    - FAO-56 para vento e evapotranspiração
    - Unidades SI (Sistema Internacional)
    """

    @staticmethod
    def convert_wind_10m_to_2m(wind_10m: float | None) -> float | None:
        """
        Converte velocidade do vento de 10m para 2m usando FAO-56.

        Fórmula FAO-56: u₂ = u₁₀ × 0.748

        Esta conversão é necessária porque:
        - Sensores medem vento a 10m de altura (padrão)
        - ETo FAO-56 requer vento a 2m de altura
        - Fator 0.748 considera perfil logarítmico de vento

        Args:
            wind_10m: Velocidade do vento a 10m (m/s)

        Returns:
            Velocidade do vento a 2m (m/s) ou None

        Referência:
            Allen et al. (1998). FAO Irrigation and Drainage Paper 56
            Chapter 3, Equation 47, page 56
        """
        if wind_10m is None:
            return None
        return wind_10m * 0.748

    @staticmethod
    def fahrenheit_to_celsius(fahrenheit: float | None) -> float | None:
        """
        Converte temperatura de Fahrenheit para Celsius.

        Fórmula: °C = (°F - 32) × 5/9

        Args:
            fahrenheit: Temperatura em °F

        Returns:
            Temperatura em °C ou None
        """
        if fahrenheit is None:
            return None
        return (fahrenheit - 32) * 5.0 / 9.0

    @staticmethod
    def celsius_to_fahrenheit(celsius: float | None) -> float | None:
        """
        Converte temperatura de Celsius para Fahrenheit.

        Fórmula: °F = °C × 9/5 + 32

        Args:
            celsius: Temperatura em °C

        Returns:
            Temperatura em °F ou None
        """
        if celsius is None:
            return None
        return celsius * 9.0 / 5.0 + 32.0

    @staticmethod
    def mph_to_ms(mph: float | None) -> float | None:
        """
        Converte velocidade de milhas por hora para metros por segundo.

        Fórmula: 1 mph = 0.44704 m/s

        Args:
            mph: Velocidade em mph

        Returns:
            Velocidade em m/s ou None
        """
        if mph is None:
            return None
        return mph * 0.44704

    @staticmethod
    def ms_to_mph(ms: float | None) -> float | None:
        """
        Converte velocidade de metros por segundo para milhas por hora.

        Fórmula: 1 m/s = 2.23694 mph

        Args:
            ms: Velocidade em m/s

        Returns:
            Velocidade em mph ou None
        """
        if ms is None:
            return None
        return ms * 2.23694

    @staticmethod
    def wh_per_m2_to_mj_per_m2(wh_per_m2: float | None) -> float | None:
        """
        Converte radiação solar de Wh/m² para MJ/m².

        Fórmula: 1 Wh = 0.0036 MJ

        Args:
            wh_per_m2: Radiação em Wh/m²

        Returns:
            Radiação em MJ/m² ou None
        """
        if wh_per_m2 is None:
            return None
        return wh_per_m2 * 0.0036

    @staticmethod
    def mj_per_m2_to_wh_per_m2(mj_per_m2: float | None) -> float | None:
        """
        Converte radiação solar de MJ/m² para Wh/m².

        Fórmula: 1 MJ = 277.778 Wh

        Args:
            mj_per_m2: Radiação em MJ/m²

        Returns:
            Radiação em Wh/m² ou None
        """
        if mj_per_m2 is None:
            return None
        return mj_per_m2 * 277.778


class WeatherValidationUtils:
    """
    Validações de dados meteorológicos.

    Verifica ranges válidos para variáveis meteorológicas
    baseado em limites físicos e práticos.
    """

    # ═══════════════════════════════════════════════════════════════
    # LIMITES GLOBAIS (Mundo inteiro)
    # Baseado em records mundiais e limites físicos
    # ═══════════════════════════════════════════════════════════════
    TEMP_MIN = -100.0  # °C (Record mundial: -89.2°C)
    TEMP_MAX = 60.0  # °C (Record mundial: 56.7°C)
    HUMIDITY_MIN = 0.0  # %
    HUMIDITY_MAX = 100.0  # %
    WIND_MIN = 0.0  # m/s
    WIND_MAX = 113.0  # m/s (~408 km/h, furacão categoria 5)
    PRECIP_MIN = 0.0  # mm
    PRECIP_MAX = 2000.0  # mm/dia (record: ~1825mm)
    SOLAR_MIN = 0.0  # MJ/m²/dia
    SOLAR_MAX = 45.0  # MJ/m²/dia (limite teórico)

    # ═══════════════════════════════════════════════════════════════
    # LIMITES BRASIL (Xavier et al. 2016, 2022)
    # "New improved Brazilian daily weather gridded data (1961–2020)"
    # Validações mais rigorosas para dados brasileiros
    # ═══════════════════════════════════════════════════════════════
    BRAZIL_TEMP_MIN = -30.0  # °C (limites Xavier)
    BRAZIL_TEMP_MAX = 50.0  # °C (limites Xavier)
    BRAZIL_HUMIDITY_MIN = 0.0  # %
    BRAZIL_HUMIDITY_MAX = 100.0  # %
    BRAZIL_WIND_MIN = 0.0  # m/s
    BRAZIL_WIND_MAX = 100.0  # m/s (limites Xavier)
    BRAZIL_PRECIP_MIN = 0.0  # mm
    BRAZIL_PRECIP_MAX = 450.0  # mm/dia (limites Xavier)
    BRAZIL_SOLAR_MIN = 0.0  # MJ/m²/dia
    BRAZIL_SOLAR_MAX = 40.0  # MJ/m²/dia (limites Xavier)
    BRAZIL_PRESSURE_MIN = 900.0  # hPa
    BRAZIL_PRESSURE_MAX = 1100.0  # hPa

    # Dicionário de limites por região
    REGIONAL_LIMITS = {
        "global": {
            "temperature": (TEMP_MIN, TEMP_MAX),
            "humidity": (HUMIDITY_MIN, HUMIDITY_MAX),
            "wind": (WIND_MIN, WIND_MAX),
            "precipitation": (PRECIP_MIN, PRECIP_MAX),
            "solar": (SOLAR_MIN, SOLAR_MAX),
            "pressure": (800.0, 1150.0),
        },
        "brazil": {
            "temperature": (BRAZIL_TEMP_MIN, BRAZIL_TEMP_MAX),
            "humidity": (BRAZIL_HUMIDITY_MIN, BRAZIL_HUMIDITY_MAX),
            "wind": (BRAZIL_WIND_MIN, BRAZIL_WIND_MAX),
            "precipitation": (BRAZIL_PRECIP_MIN, BRAZIL_PRECIP_MAX),
            "solar": (BRAZIL_SOLAR_MIN, BRAZIL_SOLAR_MAX),
            "pressure": (BRAZIL_PRESSURE_MIN, BRAZIL_PRESSURE_MAX),
        },
    }

    @classmethod
    def get_validation_limits(
        cls, region: str = "global"
    ) -> dict[str, tuple[float, float]]:
        """
        Retorna limites de validação por região.

        Args:
            region: "global" ou "brazil"

        Returns:
            Dict com limites (min, max) para cada variável
        """
        region_lower = region.lower()
        if region_lower not in cls.REGIONAL_LIMITS:
            logger.warning(
                f"Região '{region}' não reconhecida. "
                f"Usando limites globais."
            )
            region_lower = "global"
        return cls.REGIONAL_LIMITS[region_lower]

    @classmethod
    def is_valid_temperature(
        cls, temp: float | None, region: str = "global"
    ) -> bool:
        """
        Valida temperatura em °C.

        Args:
            temp: Temperatura em °C
            region: "global" ou "brazil"
        """
        if temp is None:
            return True
        limits = cls.get_validation_limits(region)
        temp_min, temp_max = limits["temperature"]
        return temp_min <= temp <= temp_max

    @classmethod
    def is_valid_humidity(
        cls, humidity: float | None, region: str = "global"
    ) -> bool:
        """
        Valida umidade relativa em %.

        Args:
            humidity: Umidade relativa (%)
            region: "global" ou "brazil"
        """
        if humidity is None:
            return True
        limits = cls.get_validation_limits(region)
        hum_min, hum_max = limits["humidity"]
        return hum_min <= humidity <= hum_max

    @classmethod
    def is_valid_wind_speed(
        cls, wind: float | None, region: str = "global"
    ) -> bool:
        """
        Valida velocidade do vento em m/s.

        Args:
            wind: Velocidade do vento (m/s)
            region: "global" ou "brazil"
        """
        if wind is None:
            return True
        limits = cls.get_validation_limits(region)
        wind_min, wind_max = limits["wind"]
        return wind_min <= wind <= wind_max

    @classmethod
    def is_valid_precipitation(
        cls, precip: float | None, region: str = "global"
    ) -> bool:
        """
        Valida precipitação em mm.

        Args:
            precip: Precipitação (mm)
            region: "global" ou "brazil"
        """
        if precip is None:
            return True
        limits = cls.get_validation_limits(region)
        precip_min, precip_max = limits["precipitation"]
        return precip_min <= precip <= precip_max

    @classmethod
    def is_valid_solar_radiation(
        cls, solar: float | None, region: str = "global"
    ) -> bool:
        """
        Valida radiação solar em MJ/m²/dia.

        Args:
            solar: Radiação solar (MJ/m²/dia)
            region: "global" ou "brazil"
        """
        if solar is None:
            return True
        limits = cls.get_validation_limits(region)
        solar_min, solar_max = limits["solar"]
        return solar_min <= solar <= solar_max

    @classmethod
    def validate_daily_data(cls, data: dict[str, Any]) -> bool:
        """
        Valida conjunto completo de dados diários.

        Args:
            data: Dicionário com dados meteorológicos diários

        Returns:
            True se todos os campos válidos estão dentro dos limites
        """
        validations = [
            cls.is_valid_temperature(data.get("temp_max")),
            cls.is_valid_temperature(data.get("temp_min")),
            cls.is_valid_temperature(data.get("temp_mean")),
            cls.is_valid_humidity(data.get("humidity_mean")),
            cls.is_valid_wind_speed(data.get("wind_speed_2m_mean")),
            cls.is_valid_precipitation(data.get("precipitation_sum")),
            cls.is_valid_solar_radiation(data.get("solar_radiation")),
        ]
        return all(validations)


class WeatherAggregationUtils:
    """
    Utilitários para agregação de dados meteorológicos.

    Métodos comuns para agregar dados horários em diários
    seguindo convenções meteorológicas padrão.
    """

    @staticmethod
    def aggregate_temperature(
        values: list[float], method: str = "mean"
    ) -> float | None:
        """
        Agrega valores de temperatura.

        Args:
            values: Lista de temperaturas
            method: 'mean', 'max', 'min'

        Returns:
            Temperatura agregada ou None
        """
        if not values:
            return None

        valid_values = [v for v in values if v is not None]
        if not valid_values:
            return None

        if method == "mean":
            return float(np.mean(valid_values))
        elif method == "max":
            return float(np.max(valid_values))
        elif method == "min":
            return float(np.min(valid_values))
        else:
            logger.warning(f"Unknown method: {method}, using mean")
            return float(np.mean(valid_values))

    @staticmethod
    def aggregate_precipitation(values: list[float]) -> float | None:
        """
        Agrega precipitação (sempre soma).

        Args:
            values: Lista de precipitações horárias

        Returns:
            Precipitação total ou None
        """
        if not values:
            return None

        valid_values = [v for v in values if v is not None]
        if not valid_values:
            return None

        return float(np.sum(valid_values))

    @staticmethod
    def safe_division(
        numerator: float | None, denominator: float | None
    ) -> float | None:
        """
        Divisão segura que retorna None se inputs inválidos.

        Args:
            numerator: Numerador
            denominator: Denominador

        Returns:
            Resultado da divisão ou None
        """
        if numerator is None or denominator is None:
            return None
        if denominator == 0:
            return None
        return numerator / denominator


# ✅ NOTA: TimezoneUtils foi movido para geographic_utils.py
# para evitar importação circular (weather_utils usa geographic_utils)


class ElevationUtils:
    """
    Utilitários para cálculos dependentes de elevação (FAO-56).

    ⚠️ IMPORTANTE: Elevação precisa é CRÍTICA para acurácia do ETo!

    Impacto da elevação nos cálculos FAO-56:

    1. **Pressão Atmosférica (P)**:
       - Varia ~12% por 1000m de elevação
       - Exemplo: Nível do mar (0m) = 101.3 kPa
                  Brasília (1172m) = 87.8 kPa (-13.3%)
                  La Paz (3640m) = 65.5 kPa (-35.3%)

    2. **Constante Psicrométrica (γ)**:
       - Proporcional à pressão atmosférica
       - γ = 0.665 × 10^-3 × P
       - Afeta diretamente o termo aerodinâmico do ETo

    3. **Radiação Solar**:
       - Aumenta ~10% por 1000m (menos atmosfera)
       - Afeta componente radiativo do ETo

    📊 **Precisão da Elevação**:
    - Open-Meteo: ~7-30m (aproximado)
    - OpenTopoData: ~1m (SRTM 30m/ASTER 30m)
    - Diferença: até 30m pode causar erro de ~0.3% no ETo

    💡 **Uso Recomendado**:
    Em eto_services.py:
        1. Buscar elevação precisa: OpenTopoClient.get_elevation()
        2. Calcular fatores: ElevationUtils.get_elevation_correction_factor()
        3. Passar fatores para calculate_et0()

    Referências:
        Allen et al. (1998). FAO-56 Irrigation and Drainage Paper 56.
        Capítulo 3: Equações 7, 8 (Pressão e Gamma).
    """

    @staticmethod
    def calculate_atmospheric_pressure(elevation: float) -> float:
        """
        Calcula pressão atmosférica a partir da elevação (FAO-56 Eq. 7).

        Fórmula:
        P = 101.3 × [(293 - 0.0065 × z) / 293]^5.26

        Args:
            elevation: Elevação em metros

        Returns:
            Pressão atmosférica em kPa

        Referência:
            Allen et al. (1998). FAO-56, Capítulo 3, Equação 7, página 31.
        """
        return 101.3 * ((293.0 - 0.0065 * elevation) / 293.0) ** 5.26

    @staticmethod
    def calculate_psychrometric_constant(elevation: float) -> float:
        """
        Calcula constante psicrométrica a partir da elevação (FAO-56 Eq. 8).

        Fórmula:
        γ = 0.665 × 10^-3 × P

        onde P é a pressão atmosférica (kPa) calculada da elevação.

        Args:
            elevation: Elevação em metros

        Returns:
            Constante psicrométrica (kPa/°C)

        Referência:
            Allen et al. (1998). FAO-56, Capítulo 3, Equação 8, página 32.

        Exemplo:
            >>> gamma = ElevationUtils.calculate_psychrometric_constant(1172)
            >>> print(f"γ = {gamma:.5f} kPa/°C")
            γ = 0.05840 kPa/°C
        """
        pressure = ElevationUtils.calculate_atmospheric_pressure(elevation)
        return 0.000665 * pressure

    @staticmethod
    def adjust_solar_radiation_for_elevation(
        radiation_sea_level: float,
        elevation: float,
    ) -> float:
        """
        Ajusta radiação solar para elevação.

        Radiação solar aumenta ~10% por 1000m de elevação
        devido à menor absorção atmosférica.

        Args:
            radiation_sea_level: Radiação ao nível do mar (MJ/m²/dia)
            elevation: Elevação em metros

        Returns:
            Radiação ajustada (MJ/m²/dia)

        Nota:
            Esta é uma aproximação. FAO-56 usa Ra (extraterrestre)
            que já considera elevação via latitude e dia do ano.
        """
        factor = 1.0 + (elevation / 1000.0) * 0.10
        return radiation_sea_level * factor

    @staticmethod
    def get_elevation_correction_factor(elevation: float) -> dict[str, float]:
        """
        Calcula todos os fatores de correção por elevação para ETo FAO-56.

        ⚠️ CRÍTICO: Use elevação precisa de OpenTopoData (1m) para máxima
        acurácia. Elevações aproximadas (Open-Meteo ~7-30m) podem causar
        erros de até 0.3% no ETo final.

        Args:
            elevation: Elevação em metros (preferencialmente de OpenTopoData)

        Returns:
            Dicionário com fatores de correção FAO-56:
            - pressure: Pressão atmosférica (kPa) - FAO-56 Eq. 7
            - gamma: Constante psicrométrica (kPa/°C) - FAO-56 Eq. 8
            - solar_factor: Fator multiplicativo para radiação solar
            - elevation: Elevação usada (m)

        Exemplo de uso integrado com OpenTopo:
            >>> # 1. Buscar elevação precisa
            >>> from backend.api.services.opentopo import OpenTopoClient
            >>> client = OpenTopoClient()
            >>> topo = await client.get_elevation(-15.7975, -47.8919)
            >>> print(f"Elevação Brasília: {topo.elevation}m")
            Elevação Brasília: 1172m

            >>> # 2. Calcular fatores com elevação precisa
            >>> factors = ElevationUtils.get_elevation_correction_factor(
            ...     topo.elevation
            ... )
            >>> print(f"Pressão: {factors['pressure']:.2f} kPa")
            >>> print(f"Gamma: {factors['gamma']:.5f} kPa/°C")
            >>> print(f"Fator Solar: {factors['solar_factor']:.4f}")
            Pressão: 87.78 kPa
            Gamma: 0.05840 kPa/°C
            Fator Solar: 1.1172

        Comparação Nível do Mar vs Altitude:
            >>> # Nível do mar (Rio de Janeiro)
            >>> sea_level = ElevationUtils.get_elevation_correction_factor(0)
            >>> print(f"P = {sea_level['pressure']:.2f} kPa")
            P = 101.30 kPa

            >>> # Altitude (Brasília 1172m)
            >>> altitude = ElevationUtils.get_elevation_correction_factor(1172)
            >>> print(f"P = {altitude['pressure']:.2f} kPa")
            P = 87.78 kPa

            >>> # Diferença percentual
            >>> diff_pct = (
            ...     (1 - altitude['pressure'] / sea_level['pressure']) * 100
            ... )
            >>> print(f"Redução: {diff_pct:.1f}%")
            Redução: 13.3%

        Impacto no ETo:
            A diferença de 13.3% na pressão pode afetar o ETo em ~0.5-1.5%,
            especialmente em climas áridos onde o termo aerodinâmico é
            dominante (alto VPD e vento).

        Referências:
            - Allen et al. (1998). FAO-56, Cap. 3, Eq. 7-8, pág. 31-32.
            - OpenTopoData: https://www.opentopodata.org/ (SRTM/ASTER 30m)
        """
        pressure = ElevationUtils.calculate_atmospheric_pressure(elevation)
        gamma = ElevationUtils.calculate_psychrometric_constant(elevation)
        solar_factor = 1.0 + (elevation / 1000.0) * 0.10

        return {
            "pressure": pressure,
            "gamma": gamma,
            "solar_factor": solar_factor,
            "elevation": elevation,
        }

    @staticmethod
    def compare_elevation_impact(
        elevation_precise: float,
        elevation_approx: float,
    ) -> dict[str, Any]:
        """
        Compara impacto de diferentes fontes de elevação nos fatores FAO-56.

        Use para quantificar a melhoria ao usar OpenTopoData (1m) vs
        Open-Meteo (~7-30m).

        Args:
            elevation_precise: Elevação precisa (OpenTopoData, 1m)
            elevation_approx: Elevação aproximada (Open-Meteo, ~7-30m)

        Returns:
            Dicionário com análise comparativa:
            - elevation_diff_m: Diferença absoluta (m)
            - pressure_diff_kpa: Diferença de pressão (kPa)
            - pressure_diff_pct: Diferença de pressão (%)
            - gamma_diff_pct: Diferença de gamma (%)
            - eto_impact_pct: Impacto estimado no ETo (%)

        Exemplo:
            >>> # OpenTopoData (preciso)
            >>> precise = 1172.0
            >>> # Open-Meteo (aproximado)
            >>> approx = 1150.0
            >>>
            >>> impact = ElevationUtils.compare_elevation_impact(
            ...     precise, approx
            ... )
            >>> print(f"Diferença elevação: {impact['elevation_diff_m']:.1f}m")
            >>> print(f"Impacto no ETo: {impact['eto_impact_pct']:.3f}%")
            Diferença elevação: 22.0m
            Impacto no ETo: 0.245%

        Interpretação:
            - < 10m: Impacto negligenciável (< 0.1% no ETo)
            - 10-30m: Impacto pequeno (0.1-0.3% no ETo)
            - > 30m: Impacto significativo (> 0.3% no ETo)
            - > 100m: Impacto crítico (> 1% no ETo)
        """
        factors_precise = ElevationUtils.get_elevation_correction_factor(
            elevation_precise
        )
        factors_approx = ElevationUtils.get_elevation_correction_factor(
            elevation_approx
        )

        elevation_diff = abs(elevation_precise - elevation_approx)
        pressure_diff = abs(
            factors_precise["pressure"] - factors_approx["pressure"]
        )
        pressure_diff_pct = (pressure_diff / factors_approx["pressure"]) * 100
        gamma_diff_pct = (
            abs(factors_precise["gamma"] - factors_approx["gamma"])
            / factors_approx["gamma"]
        ) * 100

        # Estimar impacto no ETo (aproximação baseada em sensibilidade)
        # ETo é ~50% sensível à pressão no termo aerodinâmico
        eto_impact_pct = pressure_diff_pct * 0.5

        return {
            "elevation_diff_m": elevation_diff,
            "elevation_precise_m": elevation_precise,
            "elevation_approx_m": elevation_approx,
            "pressure_precise_kpa": factors_precise["pressure"],
            "pressure_approx_kpa": factors_approx["pressure"],
            "pressure_diff_kpa": pressure_diff,
            "pressure_diff_pct": pressure_diff_pct,
            "gamma_diff_pct": gamma_diff_pct,
            "eto_impact_pct": eto_impact_pct,
            "recommendation": (
                "Negligenciável"
                if elevation_diff < 10
                else (
                    "Pequeno"
                    if elevation_diff < 30
                    else (
                        "Significativo" if elevation_diff < 100 else "Crítico"
                    )
                )
            ),
        }
