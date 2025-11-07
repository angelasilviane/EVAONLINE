"""
Climate Sources Routes
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Query

router = APIRouter(prefix="/climate/sources", tags=["Climate"])


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
        # Fontes globais (sempre disponíveis)
        global_sources = [
            {
                "id": "openmeteo_archive",
                "name": "Open-Meteo Archive",
                "type": "global",
                "coverage": "worldwide",
                "data_types": ["temperature", "humidity", "wind", "radiation"],
                "temporal_range": "1940-present",
            },
            {
                "id": "nasa_power",
                "name": "NASA POWER",
                "type": "global",
                "coverage": "worldwide",
                "data_types": ["temperature", "humidity", "wind", "radiation"],
                "temporal_range": "1981-present",
            },
        ]

        result = {
            "global_sources": global_sources,
            "regional_sources": [],
            "total_sources": len(global_sources),
        }

        # Se lat/lon fornecidos, adicionar fontes regionais (Brasil)
        if lat is not None and lon is not None:
            # Verificar se está no Brasil (-34 a 5.27 lat, -73.99 a -28.84 lon)
            if -34 <= lat <= 5.27 and -73.99 <= lon <= -28.84:
                regional = [
                    {
                        "id": "inmet",
                        "name": "INMET (Instituto Nacional de Meteorologia)",
                        "type": "regional",
                        "coverage": "Brazil",
                        "data_types": [
                            "temperature",
                            "humidity",
                            "wind",
                            "radiation",
                            "precipitation",
                        ],
                        "temporal_range": "2000-present",
                    }
                ]
                result["regional_sources"] = regional
                result["total_sources"] += len(regional)

        return result

    except Exception as e:
        return {
            "error": str(e),
            "global_sources": [],
            "regional_sources": [],
            "total_sources": 0,
        }
