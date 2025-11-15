"""
ETo Calculation Routes
"""

import time
from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from loguru import logger

from backend.database.connection import get_db
from backend.database.models.user_favorites import UserFavorites

# Importar 5 módulos de clima
from backend.api.services.climate_validation import ClimateValidationService
from backend.api.services.climate_source_availability import (
    OperationMode,
)
from backend.api.services.climate_source_manager import ClimateSourceManager

# Mapeamento de period_type para OperationMode
# Centraliza conversão de strings antigas para novo enum
OPERATION_MODE_MAPPING = {
    "historical_email": OperationMode.HISTORICAL_EMAIL,
    "dashboard_current": OperationMode.DASHBOARD_CURRENT,
    "dashboard_forecast": OperationMode.DASHBOARD_FORECAST,
}

eto_router = APIRouter(prefix="/internal/eto", tags=["ETo"])


# ============================================================================
# SCHEMAS
# ============================================================================


class EToCalculationRequest(BaseModel):
    """Request para cálculo ETo."""

    lat: float
    lng: float
    start_date: str
    end_date: str
    sources: Optional[str] = "auto"
    period_type: Optional[str] = "dashboard"  # historical, dashboard, forecast
    elevation: Optional[float] = None
    estado: Optional[str] = None
    cidade: Optional[str] = None


class LocationInfoRequest(BaseModel):
    """Request para informações de localização."""

    lat: float
    lng: float


class FavoriteRequest(BaseModel):
    """Request para favoritos."""

    user_id: str = "default"
    name: str
    lat: float
    lng: float
    cidade: Optional[str] = None
    estado: Optional[str] = None


# ============================================================================
# ENDPOINTS ESSENCIAIS (5)
# ============================================================================


@eto_router.post("/calculate")
async def calculate_eto(
    request: EToCalculationRequest, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    ✅ Cálculo ETo principal (configurável).

    Suporta:
    - Múltiplas fontes de dados
    - Auto-detecção de melhor fonte
    - Fusão de dados (Kalman)
    - Cache automático

    Modos de operação (period_type):
    - historical_email: 1-90 dias (apenas NASA POWER e OpenMeteo Archive)
    - dashboard_current: 7-30 dias (todas as APIs disponíveis)
    - dashboard_forecast: hoje até hoje+5d (apenas APIs de previsão)
    """
    try:
        from backend.core.eto_calculation.eto_services import (
            EToProcessingService,
        )

        # 0. Normalizar period_type para OperationMode
        period_type_str = (request.period_type or "dashboard_current").lower()

        # Usar mapeamento centralizado
        operation_mode = OPERATION_MODE_MAPPING.get(
            period_type_str, OperationMode.DASHBOARD_CURRENT
        )

        # 1. Usar ClimateValidationService
        validator = ClimateValidationService()
        is_valid, validation_result = validator.validate_all(
            lat=request.lat,
            lon=request.lng,
            start_date=request.start_date,
            end_date=request.end_date,
            variables=["et0_fao_evapotranspiration"],
            source="auto",
            mode=operation_mode,
        )

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Validação falhou: "
                    f"{validation_result.get('errors', [])}"
                ),
            )

        # 2. Converter datas para datetime objects para manager
        start_dt = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(request.end_date, "%Y-%m-%d")

        # 3. Usar ClimateSourceManager para seleção
        manager = ClimateSourceManager()

        if request.sources == "auto" or not request.sources:
            # Auto-seleção usando validate_and_select_source
            source_id, source_info = manager.validate_and_select_source(
                lat=request.lat,
                lon=request.lng,
                start_date=start_dt,
                end_date=end_dt,
                mode=operation_mode,
                preferred_source=None,
            )

            if not source_id:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Nenhuma fonte disponível: "
                        f"{source_info.get('reason', 'Unknown error')}"
                    ),
                )

            selected_source = source_id
            logger.info(
                f"Auto-seleção: {operation_mode.value} em "
                f"({request.lat}, {request.lng}) → {source_id}"
            )
        else:
            # Validar fonte especificada
            selected_source = request.sources
            is_compatible, compat_reason = manager.validate_source_for_context(
                source_id=selected_source,
                mode=operation_mode,
                start_date=start_dt,
                end_date=end_dt,
            )

            if not is_compatible:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Fonte '{selected_source}' incompatível: "
                        f"{compat_reason}"
                    ),
                )

            logger.info(f"Fontes especificadas: {selected_source}")
            source_info = None

        # 4. Obter elevação (se não fornecida)
        elevation = request.elevation
        if elevation is None:
            logger.info(
                f"Elevação não fornecida para ({request.lat}, {request.lng}), "
                f"será obtida via API"
            )

        # 5. Executar cálculo ETo
        service = EToProcessingService(db_session=db)
        result = await service.process_location(
            latitude=request.lat,
            longitude=request.lng,
            start_date=request.start_date,
            end_date=request.end_date,
            elevation=elevation,
            include_recomendations=False,
            database=selected_source,
        )

        # 6. Retornar resultados
        return {
            "status": "success",
            "data": result.get("eto_data", []),
            "statistics": result.get("statistics", {}),
            "source": selected_source,
            "source_info": source_info,
            "operation_mode": operation_mode.value,
            "warnings": result.get("warnings", []),
            "location": {
                "lat": request.lat,
                "lng": request.lng,
                "elevation_m": elevation,
            },
            "period": {
                "start": request.start_date,
                "end": request.end_date,
            },
            "timestamp": time.time(),
        }

    except ValueError as ve:
        raise HTTPException(
            status_code=400, detail=f"Formato de data inválido: {str(ve)}"
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"ETo calculation failed: {str(e)}"
        )


@eto_router.post("/location-info")
async def get_location_info(request: LocationInfoRequest) -> Dict[str, Any]:
    """
    ✅ Informações de localização (timezone, elevação).
    """
    try:
        # TODO: Implementar busca real de timezone e elevação
        # Por enquanto, retorna estrutura básica
        return {
            "status": "success",
            "location": {
                "lat": request.lat,
                "lng": request.lng,
                "timezone": "America/Sao_Paulo",  # Placeholder
                "elevation_m": None,  # Placeholder
            },
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get location info: {str(e)}"
        )


@eto_router.post("/favorites/add")
async def add_favorite(
    request: FavoriteRequest, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    ✅ Adicionar favorito.
    """
    try:
        # Verificar duplicata
        existing = (
            db.query(UserFavorites)
            .filter_by(
                user_id=request.user_id, lat=request.lat, lng=request.lng
            )
            .first()
        )

        if existing:
            return {
                "status": "exists",
                "message": "Favorito já existe",
                "favorite_id": existing.id,
            }

        # Criar novo favorito
        favorite = UserFavorites(
            user_id=request.user_id,
            name=request.name,
            lat=request.lat,
            lng=request.lng,
            cidade=request.cidade,
            estado=request.estado,
        )
        db.add(favorite)
        db.commit()
        db.refresh(favorite)

        return {
            "status": "success",
            "message": "Favorito adicionado",
            "favorite_id": favorite.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to add favorite: {str(e)}"
        )


@eto_router.get("/favorites/list")
async def list_favorites(
    user_id: str = "default", db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    ✅ Listar favoritos do usuário.
    """
    try:
        favorites = (
            db.query(UserFavorites)
            .filter_by(user_id=user_id)
            .order_by(UserFavorites.created_at.desc())
            .all()
        )

        return {
            "status": "success",
            "total": len(favorites),
            "favorites": [
                {
                    "id": f.id,
                    "name": f.name,
                    "lat": f.lat,
                    "lng": f.lng,
                    "cidade": f.cidade,
                    "estado": f.estado,
                    "created_at": f.created_at.isoformat(),
                }
                for f in favorites
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list favorites: {str(e)}"
        )


@eto_router.delete("/favorites/remove/{favorite_id}")
async def remove_favorite(
    favorite_id: int, user_id: str = "default", db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    ✅ Remover favorito.
    """
    try:
        favorite = (
            db.query(UserFavorites)
            .filter_by(id=favorite_id, user_id=user_id)
            .first()
        )

        if not favorite:
            raise HTTPException(
                status_code=404, detail="Favorito não encontrado"
            )

        db.delete(favorite)
        db.commit()

        return {
            "status": "success",
            "message": "Favorito removido",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to remove favorite: {str(e)}"
        )
