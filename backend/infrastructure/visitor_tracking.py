import asyncio
from datetime import datetime

import redis
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import VisitorStats


class VisitorTracker:
    """
    Rastreia visitantes com garantia de persistência.

    Estratégia:
    1. Redis: contagem rápida e em tempo real
    2. PostgreSQL: persistência permanente
    3. Sincronização: a cada 1h ou 100 visitantes
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.redis_key = "visitors:total"
        self.redis_temp_key = "visitors:session"
        self.sync_threshold = 100  # Sincronizar a cada 100 visitas
        self.sync_interval = 3600  # Ou a cada 1 hora

    async def increment_visitor(self, session_id: str = None) -> int:
        """
        Incrementa contador de visitantes.

        Strategy:
        1. Redis: increment fast (no disk I/O)
        2. Return current count
        3. Background: persist periodically
        """
        # Incrementar no Redis
        current_count = self.redis.incr(self.redis_key)

        # Adicionar session a set (para analytics)
        if session_id:
            self.redis.sadd(self.redis_temp_key, session_id)

        # Se atingir threshold, sincronizar com DB
        if current_count % self.sync_threshold == 0:
            asyncio.create_task(self._sync_to_database(current_count))

        return current_count

    async def _sync_to_database(self, count: int, db: Session = None):
        """Sincroniza contagem Redis → PostgreSQL"""
        if db is None:
            db = next(get_db())

        try:
            stats = db.query(VisitorStats).first()
            if stats:
                stats.total_visitors = count
                stats.last_sync = datetime.utcnow()
            else:
                stats = VisitorStats(total_visitors=count, last_sync=datetime.utcnow())
                db.add(stats)

            db.commit()
            print(f"✅ Visitantes sincronizados: {count}")
        except Exception as e:
            print(f"❌ Erro sincronização: {e}")
            db.rollback()

    async def get_total_visitors(self) -> int:
        """
        Retorna total de visitantes.
        Combina Redis + PostgreSQL para garantir valores corretos.
        """
        redis_count = int(self.redis.get(self.redis_key) or 0)

        # Se Redis está vazio, restaurar do PostgreSQL
        if redis_count == 0:
            db = next(get_db())
            stats = db.query(VisitorStats).first()
            if stats:
                redis_count = stats.total_visitors
                self.redis.set(self.redis_key, redis_count)

        return redis_count

    def get_unique_sessions_today(self) -> int:
        """Retorna sessions únicas hoje"""
        return self.redis.scard(self.redis_temp_key)
