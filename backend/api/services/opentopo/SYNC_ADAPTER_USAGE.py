"""
OpenTopoData Sync Adapter - Documentação de Uso.

Fornece interface síncrona para busca de dados de elevação,
facilitando integração com Celery tasks, scripts offline
e código síncrono legado.
"""

# ============================================================================
# 1. USAR EM CELERY TASKS (SÍNCRONO)
# ============================================================================

from celery import shared_task
from backend.api.services.opentopo import OpenTopoSyncAdapter


@shared_task
def calculate_eto_with_elevation(lat: float, lon: float) -> dict:
    """
    Calcular ETo considerando elevação do terreno.

    Usa OpenTopoSyncAdapter porque Celery tasks são síncronas.
    """
    adapter = OpenTopoSyncAdapter()

    # Buscar elevação (SÍNCRONO)
    location = adapter.get_elevation_sync(lat, lon)

    if not location:
        return {"error": "Elevation data not available"}

    # Usar elevação em cálculos de ETo FAO-56
    from backend.api.services.weather_utils import ElevationUtils

    elevation = location.elevation
    pressure = ElevationUtils.calculate_atmospheric_pressure(elevation)
    gamma = ElevationUtils.calculate_psychrometric_constant(elevation)

    return {
        "lat": lat,
        "lon": lon,
        "elevation": elevation,
        "atmospheric_pressure_kpa": pressure,
        "psychrometric_constant": gamma,
        "dataset": location.dataset,
    }


# ============================================================================
# 2. USAR EM SCRIPTS OFFLINE / BATCH DOWNLOAD
# ============================================================================


def batch_download_elevations(locations_file: str):
    """
    Baixar elevações para múltiplas localizações (batch).

    Arquivo CSV: lat,lon,name
    """
    import pandas as pd

    adapter = OpenTopoSyncAdapter()
    df = pd.read_csv(locations_file)

    locations = list(zip(df["lat"], df["lon"]))

    # Buscar em batch (mais eficiente, máx 100 por request)
    results = adapter.get_elevations_batch_sync(locations)

    df["elevation"] = [
        r.elevation if i < len(results) else None
        for i, r in enumerate(results)
    ]
    df["dataset"] = [
        r.dataset if i < len(results) else None for i, r in enumerate(results)
    ]

    df.to_csv("elevations_output.csv", index=False)
    print(f"✅ {len(results)} elevações salvadas")


# ============================================================================
# 3. USAR EM CÓDIGO SÍNCRONO LEGADO
# ============================================================================


def legacy_weather_calculation():
    """
    Código síncrono legado que precisa de elevação.
    """
    adapter = OpenTopoSyncAdapter()

    # Ponto único
    brasilia = adapter.get_elevation_sync(-15.7801, -47.9292)
    if brasilia:
        print(f"Brasília: {brasilia.elevation}m ({brasilia.dataset})")

    # Verificar cobertura
    in_coverage = adapter.is_in_coverage_sync(78.2232, 15.6267)  # Svalbard
    print(f"Svalbard in SRTM coverage: {in_coverage}")  # False (usa ASTER)


# ============================================================================
# 4. USAR PARA HEALTH CHECKS E MONITORAMENTO
# ============================================================================


def monitor_opentopo_api():
    """
    Health check para OpenTopoData API.
    """
    adapter = OpenTopoSyncAdapter()

    is_healthy = adapter.health_check_sync()

    if is_healthy:
        print("✅ OpenTopoData API está acessível")
    else:
        print("❌ OpenTopoData API está indisponível")

    # Info sobre cobertura
    info = adapter.get_coverage_info()
    print(f"Datasets: {list(info['datasets'].keys())}")
    print(f"Rate limit: {info['rate_limits']['requests_per_second']} req/s")
    print(f"Cache TTL: {info['cache_strategy']['ttl_human']}")


# ============================================================================
# 5. COMPARAÇÃO: ASYNC vs SYNC
# ============================================================================

"""
ASYNC CLIENT (OpenTopoClient):
- Melhor para: Aplicações async, FastAPI routes, aiohttp
- Uso:
    from backend.api.services.opentopo import OpenTopoClient
    
    async def get_elevation():
        client = OpenTopoClient()
        location = await client.get_elevation(lat, lon)
        await client.close()
        return location

SYNC ADAPTER (OpenTopoSyncAdapter):
- Melhor para: Celery tasks, scripts offline, código legado
- Uso:
    from backend.api.services.opentopo import OpenTopoSyncAdapter
    
    def get_elevation():
        adapter = OpenTopoSyncAdapter()
        location = adapter.get_elevation_sync(lat, lon)
        return location
"""

# ============================================================================
# 6. RATE LIMITS E BOAS PRÁTICAS
# ============================================================================

"""
OpenTopoData Rate Limits (2025):
- ✅ 1 request/segundo
- ✅ 1000 requests/dia
- ✅ 100 locations/request

Boas Práticas:
1. ✅ Use batch_sync para múltiplas localizações (até 100)
2. ✅ Habilite cache Redis (TTL: 30 dias, elevação não muda)
3. ✅ Evite requests duplicadas (mesmas coordenadas)
4. ✅ Use auto-switch (SRTM→ASTER para lat > 60°)
5. ✅ Trate erros gracefully (None return)

Exemplo com Cache:
    from backend.infrastructure.cache import ClimateCache
    
    cache = ClimateCache()
    adapter = OpenTopoSyncAdapter(cache=cache)
    
    # Primera request: busca da API
    location1 = adapter.get_elevation_sync(-15.7801, -47.9292)
    
    # Segunda request (mesmas coordenadas): retorna do cache
    location2 = adapter.get_elevation_sync(-15.7801, -47.9292)
"""

# ============================================================================
# 7. DATASETS E COBERTURA
# ============================================================================

"""
SRTM 30m (Padrão):
- Cobertura: -60° a +60° latitude
- Resolução: ~30m
- Qualidade: Excelente onde disponível
- Melhor para: Maior parte do mundo

ASTER 30m (Auto-switch para lat > 60°):
- Cobertura: Global (-90° a +90°)
- Resolução: ~30m
- Qualidade: Boa (inclui regiões polares)
- Melhor para: Regiões polares (Groenlândia, Antártida, Svalbard)

Auto-Switch:
    # Se latitude > 60°, muda automaticamente de SRTM para ASTER
    location = adapter.get_elevation_sync(78.2232, 15.6267)  # Svalbard
    # dataset: "aster30m" (não srtm30m!)
"""

# ============================================================================
# 8. TRATAMENTO DE ERROS
# ============================================================================

"""
Casos de retorno None:
1. Coordenadas inválidas (lat > 90 ou lon > 180)
2. Sem dados de elevação para ponto (raro)
3. API indisponível
4. Erro de rede

Exemplo:
    adapter = OpenTopoSyncAdapter()
    location = adapter.get_elevation_sync(lat, lon)
    
    if location is None:
        print("Elevação não disponível, usando valor padrão")
        elevation = 0  # ou valor regional padrão
    else:
        elevation = location.elevation
"""

# ============================================================================
# 9. INTEGRAÇÃO COM FAO-56
# ============================================================================

"""
ETo FAO-56 usa elevação para 3 cálculos principais:

1. Pressão Atmosférica (P):
   P = 101.3 × [(293 - 0.0065 × z) / 293]^5.26
   
   Brasília (1172m): 87.8 kPa
   São Paulo (829m): 91.0 kPa
   
2. Constante Psicrométrica (γ):
   γ = 0.665 × 10^-3 × P
   
   Brasília: 0.058 kPa/°C
   São Paulo: 0.061 kPa/°C
   
3. Radiação Solar Extraterrestre (Ra):
   Aumenta ~10% por 1000m
   
   1000m: +10%
   2000m: +20%

Implementação centralizada em:
    from backend.api.services.weather_utils import ElevationUtils
    
    P = ElevationUtils.calculate_atmospheric_pressure(elevation)
    gamma = ElevationUtils.calculate_psychrometric_constant(elevation)
    radiation_adj = ElevationUtils.adjust_solar_radiation_for_elevation(
        radiation, elevation
    )
"""
