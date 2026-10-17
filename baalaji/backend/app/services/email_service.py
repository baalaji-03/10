import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models import PharmacySetting, NotificationLog

logger = logging.getLogger("pharmacy_email")

def send_smtp_email(
    db: Session,
    subject: str,
    body_html: str,
    recipient_email: str,
    notification_type: str = "ALERT",
    attachment_bytes: Optional[BytesIO] = None,
    attachment_filename: Optional[str] = None
) -> dict:
    """
    Sends email using pharmacy SMTP settings and logs result into notification_logs.
    """
    setting = db.query(PharmacySetting).first()
    if not setting or not setting.smtp_host or not setting.smtp_user:
        error_msg = "SMTP settings are not configured. Please configure SMTP in Settings > Email Integration."
        logger.warning(error_msg)
        _log_notification(db, notification_type, recipient_email, subject, body_html, "FAILED", error_msg)
        return {"success": False, "message": error_msg}

    recipient = recipient_email or setting.alert_email_recipient
    if not recipient:
        error_msg = "No recipient email address provided."
        _log_notification(db, notification_type, recipient, subject, body_html, "FAILED", error_msg)
        return {"success": False, "message": error_msg}

    try:
        msg = MIMEMultipart()
        msg["From"] = setting.smtp_from_email or setting.smtp_user
        msg["To"] = recipient
        msg["Subject"] = subject

        msg.attach(MIMEText(body_html, "html"))

        if attachment_bytes and attachment_filename:
            part = MIMEBase("application", "octet-stream")
            attachment_bytes.seek(0)
            part.set_payload(attachment_bytes.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename=\"{attachment_filename}\""
            )
            msg.attach(part)

        # Connect to SMTP server
        if setting.smtp_use_tls:
            server = smtplib.SMTP(setting.smtp_host, setting.smtp_port, timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP(setting.smtp_host, setting.smtp_port, timeout=15)

        if setting.smtp_password:
            server.login(setting.smtp_user, setting.smtp_password)

        server.send_message(msg)
        server.quit()

        _log_notification(db, notification_type, recipient, subject, body_html, "SENT", None)
        return {"success": True, "message": f"Email successfully sent to {recipient}"}

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        _log_notification(db, notification_type, recipient, subject, body_html, "FAILED", str(e))
        return {"success": False, "message": f"SMTP Error: {str(e)}"}

def _log_notification(db: Session, n_type: str, recipient: str, subject: str, message: str, status: str, err: Optional[str]):
    try:
        notif = NotificationLog(
            notification_type=n_type,
            recipient=recipient or "N/A",
            subject=subject,
            message=message[:500] if message else "",
            status=status,
            error_message=err
        )
        db.add(notif)
        db.commit()
    except Exception as log_err:
        logger.error(f"Failed to write notification log: {log_err}")
        db.rollback()
