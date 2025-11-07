"""
Utilitários para validação e envio de emails.

Este módulo fornece funções para:
- Validação de formato de email
- Envio de emails (TODO: implementar com SMTP)
"""

import re
from typing import Optional

from loguru import logger


def validate_email(email: str) -> bool:
    """
    Valida formato do email.

    Args:
        email: Endereço de email a validar

    Returns:
        True se email válido, False caso contrário

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid.email")
        False
    """
    if not email or not isinstance(email, str):
        return False

    # Padrão RFC 5322 simplificado
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
) -> bool:
    """
    Envia email simples (texto).

    TODO: Implementar com SMTP real (ex: SendGrid, AWS SES, etc.)

    Args:
        to: Email destinatário
        subject: Assunto do email
        body: Corpo do email (texto simples)
        from_email: Email remetente (opcional, usa padrão do sistema)

    Returns:
        True se enviado com sucesso, False caso contrário
    """
    if not validate_email(to):
        logger.error(f"Email inválido: {to}")
        return False

    # TODO: Implementar envio real
    logger.info(
        f"[EMAIL SIMULADO] Para: {to}, Assunto: {subject}, "
        f"Corpo: {body[:50]}..."
    )
    return True


def send_email_with_attachment(
    to: str,
    subject: str,
    body: str,
    attachment_path: str,
    from_email: Optional[str] = None,
) -> bool:
    """
    Envia email com anexo.

    TODO: Implementar com SMTP real (ex: SendGrid, AWS SES, etc.)

    Args:
        to: Email destinatário
        subject: Assunto do email
        body: Corpo do email (texto simples)
        attachment_path: Caminho completo do arquivo anexo
        from_email: Email remetente (opcional, usa padrão do sistema)

    Returns:
        True se enviado com sucesso, False caso contrário
    """
    if not validate_email(to):
        logger.error(f"Email inválido: {to}")
        return False

    # TODO: Implementar envio real com anexo
    logger.info(
        f"[EMAIL SIMULADO COM ANEXO] Para: {to}, Assunto: {subject}, "
        f"Anexo: {attachment_path}"
    )
    return True
