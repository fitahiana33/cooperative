"""Email delivery of authorized notification titles/messages through configured SMTP.

No booking access code, checkout secret, QR or attachment is added. Existing
IN_APP history is never promoted to email. The outbox retries transport errors.
"""
import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parseaddr

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.notification import Notification
from app.models.reservation import Reservation

logger = logging.getLogger(__name__)


def _recipient(db: Session, item: Notification) -> str | None:
    user = item.user
    if user.email.endswith("@guest.cooperative.local"):
        reservation = db.get(Reservation, item.id_reservation) if item.id_reservation else None
        return reservation.email_reservataire if reservation else None
    return user.email if user.is_active else None


def _send(recipient: str, item: Notification) -> None:
    message = EmailMessage()
    message["Subject"] = item.titre
    message["From"] = settings.smtp_from or settings.smtp_username or "no-reply@cooperative.local"
    message["To"] = recipient
    domain = parseaddr(str(message["From"]))[1].rsplit("@", 1)[-1]
    message["Message-ID"] = f"<notification-{item.id}@{domain}>"
    message.set_content(item.message)
    smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_use_tls and not settings.smtp_use_ssl:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


def deliver_notifications(db: Session, limit: int = 5) -> int:
    if not settings.notification_email_enabled or not settings.smtp_host:
        return 0
    sent = 0
    for _ in range(min(limit, 20)):
        now = datetime.now(timezone.utc)
        item = db.scalar(select(Notification).where(
            Notification.canal == "EMAIL", Notification.delivery_status.in_(["PENDING", "RETRY"]),
            or_(Notification.next_attempt_at.is_(None), Notification.next_attempt_at <= now),
        ).order_by(Notification.id).with_for_update(skip_locked=True).limit(1))
        if not item:
            db.rollback()
            break
        recipient = _recipient(db, item)
        if not recipient:
            item.delivery_status = "IN_APP"
            db.commit()
            continue
        item.delivery_attempts += 1
        try:
            recipient = validate_email(recipient, check_deliverability=False).normalized
            _send(recipient, item)
        except (EmailNotValidError, ValueError):
            item.delivery_status = "FAILED"
            item.delivery_error = "Adresse ou configuration email invalide."
        except (OSError, smtplib.SMTPException):
            logger.warning("Notification email %s not delivered", item.id)
            item.delivery_status = "FAILED" if item.delivery_attempts >= 5 else "RETRY"
            item.next_attempt_at = now + timedelta(minutes=2 ** item.delivery_attempts)
            item.delivery_error = "Transport email indisponible."
        else:
            item.delivery_status = "DELIVERED"
            item.delivered_at = now
            item.delivery_error = None
            sent += 1
        db.commit()
    return sent
