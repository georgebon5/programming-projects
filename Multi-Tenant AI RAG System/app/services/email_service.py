"""
Email service — abstracts email delivery behind a simple interface.

In development the service logs emails to the console (no SMTP required).
In production it sends via SMTP when EMAIL_HOST is configured.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(*, to: str, subject: str, body: str) -> None:
    """Send a plain-text email.

    When SMTP settings are not configured (development), the email is written
    to the application log so developers can copy the link manually.
    """
    if not settings.email_host:
        logger.info(
            "EMAIL (console backend) to=%s subject=%s\n%s",
            to,
            subject,
            body,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP(settings.email_host, settings.email_port) as server:
        if settings.email_use_tls:
            server.starttls()
        if settings.email_username:
            server.login(settings.email_username, settings.email_password)
        server.send_message(msg)

    logger.info("Email sent to %s — subject: %s", to, subject)
