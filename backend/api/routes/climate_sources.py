"""
Climate Sources Routes
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from loguru import logger

from backend.api.services.climate_source_manager import ClimateSourceManager
from backend.api.services.climate_source_selector import ClimateSourceSelector

router = APIRouter(prefix="/climate/sources", tags=["Climate"])

# Inicializar gerenciador e seletor globalmente
_manager = ClimateSourceManager()
_selector = ClimateSourceSelector()


# ============================================================================
# ENDPOINT ESSENCIAL (1)
# ============================================================================


@router.get("/available")
async def get_available_sources(
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
) -> Dict[str, Any]:
    """
    ✅ Descobrir fontes de dados climáticos disponíveis.

    Args:
        lat: Latitude (opcional - se fornecida, retorna fontes regionais)
        lon: Longitude (opcional)

    Returns:
        Dict com fontes disponíveis (global + regional se lat/lon fornecidos)
    """
    try:
        # Se lat/lon não fornecidos, retornar todas as fontes
        if lat is None or lon is None:
            sources = []
            for source_id, config in _manager.SOURCES_CONFIG.items():
                sources.append(
                    {
                        "id": source_id,
                        "name": config.get("name", source_id),
                        "type": config.get("coverage", "unknown"),
                        "coverage": config.get("coverage", "unknown"),
                        "license": config.get("license", "unknown"),
                        "temporal_range": config.get("temporal_range", ""),
                        "data_types": config.get("variables", []),
                        "realtime": config.get("realtime", False),
                        "priority": config.get("priority", 0),
                    }
                )

            return {
                "status": "success",
                "sources": sources,
                "total_sources": len(sources),
                "location": None,
                "geographic_context": None,
            }

        # Com lat/lon: detectar região e retornar fontes compatíveis
        is_usa = _manager.is_in_usa(lat, lon)
        is_nordic = _manager.is_in_nordic(lat, lon)

        geographic_context = "global"
        if is_usa:
            geographic_context = "usa"
        elif is_nordic:
            geographic_context = "nordic"

        # Obter fontes disponíveis para localização
        available = _selector.get_available_sources_for_frontend(lat, lon)

        sources = []
        for source_id in available:
            if source_id in _manager.SOURCES_CONFIG:
                config = _manager.SOURCES_CONFIG[source_id]
                sources.append(
                    {
                        "id": source_id,
                        "name": config.get("name", source_id),
                        "type": config.get("coverage", "unknown"),
                        "coverage": config.get("coverage", "unknown"),
                        "license": config.get("license", "unknown"),
                        "temporal_range": config.get("temporal_range", ""),
                        "data_types": config.get("variables", []),
                        "realtime": config.get("realtime", False),
                        "priority": config.get("priority", 0),
                    }
                )

        logger.info(
            f"Available sources for ({lat}, {lon}) [{geographic_context}]: "
            f"{[s['id'] for s in sources]}"
        )

        return {
            "status": "success",
            "sources": sources,
            "total_sources": len(sources),
            "location": {"lat": lat, "lon": lon},
            "geographic_context": geographic_context,
        }

    except Exception as e:
        logger.error(f"Error getting available sources: {e}")
        return {
            "status": "error",
            "error": str(e),
            "sources": [],
            "total_sources": 0,
        }
