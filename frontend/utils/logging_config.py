"""
Configuração global de logging para o ETO Calculator.
"""

import logging


def setup_logging(level=logging.INFO):
    """
    Configura o logging básico.
    Args:
        level: Nível de log (ex: logging.DEBUG para dev).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
