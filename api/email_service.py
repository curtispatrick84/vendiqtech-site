import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@vendiqtech.com")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "hello@vendiqtech.com")


async def send_notification(subject: str, body_html: str):
    """Send an email notification. Fails silently — data is already saved in DB."""
    if not SMTP_HOST or not SMTP_USER:
        logger.warning("SMTP not configured — skipping email: %s", subject)
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = f"VendiQ <{SMTP_FROM}>"
    msg["To"] = NOTIFY_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASS,
            start_tls=True,
        )
        logger.info("Email sent: %s", subject)
    except Exception:
        logger.exception("Failed to send email: %s", subject)
