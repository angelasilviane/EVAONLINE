"""
Celery tasks package.

Tasks disponíveis:
- visitor_sync: Sincronização de visitantes
- historical_download: Processamento assíncrono de downloads históricos
"""

from backend.infrastructure.celery.tasks.historical_download import (
    process_historical_download,
)
from backend.infrastructure.celery.tasks.visitor_sync import *  # noqa: F401,F403

__all__ = [
    "process_historical_download",
]
