"""
Serviço de contagem de visitantes usando Redis + PostgreSQL
"""

from datetime import datetime
from typing import Dict, Optional

import redis
from sqlalchemy.orm import Session

from backend.database.models.visitor_stats import VisitorStats


class VisitorCounterService:
    """Gerencia contagem de visitantes em tempo real com persistência"""

    def __init__(self, redis_client: redis.Redis, db_session: Session):
        self.redis = redis_client
        self.db = db_session
        self.REDIS_KEY_VISITORS = "visitors:count"
        self.REDIS_KEY_UNIQUE_TODAY = "visitors:unique:today"
        self.REDIS_KEY_PEAK_HOUR = "visitors:peak_hour"
        self.REDIS_KEY_HOURLY = "visitors:hourly"  # Contador por hora

    def increment_visitor(self) -> Dict:
        """
        Incrementa contador de visitantes no Redis
        Retorna status atual
        """
        try:
            # Incrementar contador total
            self.redis.incr(self.REDIS_KEY_VISITORS)

            # Incrementar hora atual
            current_hour = datetime.utcnow().strftime("%H:00")
            hourly_key = f"{self.REDIS_KEY_HOURLY}:{current_hour}"
            self.redis.incr(hourly_key)
            self.redis.expire(hourly_key, 86400)  # TTL 24h

            # Obter counts
            total = int(self.redis.get(self.REDIS_KEY_VISITORS) or 0)
            hourly = int(self.redis.get(hourly_key) or 0)

            return {
                "total_visitors": total,
                "current_hour_visitors": hourly,
                "current_hour": current_hour,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_stats(self) -> Dict:
        """Retorna estatísticas atuais dos visitantes"""
        try:
            total = int(self.redis.get(self.REDIS_KEY_VISITORS) or 0)
            current_hour = datetime.utcnow().strftime("%H:00")
            hourly_key = f"{self.REDIS_KEY_HOURLY}:{current_hour}"
            hourly = int(self.redis.get(hourly_key) or 0)

            # Obter pico de hora do dia
            peak_hour = self.redis.get(self.REDIS_KEY_PEAK_HOUR)
            if peak_hour:
                peak_hour = peak_hour.decode() if isinstance(peak_hour, bytes) else peak_hour

            return {
                "total_visitors": total,
                "current_hour_visitors": hourly,
                "current_hour": current_hour,
                "peak_hour": peak_hour,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def sync_to_database(self) -> Dict:
        """
        Sincroniza dados de Redis para PostgreSQL
        Útil para persistência em longo prazo
        """
        try:
            total = int(self.redis.get(self.REDIS_KEY_VISITORS) or 0)
            current_hour = datetime.utcnow().strftime("%H:%M")

            # Buscar ou criar registro no banco
            stats = self.db.query(VisitorStats).first()
            if not stats:
                stats = VisitorStats(
                    total_visitors=total,
                    unique_visitors_today=total,
                    last_sync=datetime.utcnow(),
                    peak_hour=current_hour,
                )
                self.db.add(stats)
            else:
                stats.total_visitors = total
                stats.last_sync = datetime.utcnow()
                stats.peak_hour = current_hour

            self.db.commit()

            return {
                "status": "synced",
                "total_visitors": total,
                "last_sync": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            self.db.rollback()
            return {"error": str(e)}

    def get_database_stats(self) -> Optional[Dict]:
        """Retorna estatísticas persistidas no banco de dados"""
        try:
            stats = self.db.query(VisitorStats).first()
            if stats:
                return {
                    "total_visitors": stats.total_visitors,
                    "unique_visitors_today": stats.unique_visitors_today,
                    "peak_hour": stats.peak_hour,
                    "last_sync": (stats.last_sync.isoformat() if stats.last_sync else None),
                    "created_at": (stats.created_at.isoformat() if stats.created_at else None),
                }
            return None
        except Exception as e:
            return {"error": str(e)}
