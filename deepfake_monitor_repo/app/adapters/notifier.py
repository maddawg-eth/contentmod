from __future__ import annotations

import smtplib
from email.message import EmailMessage

from twilio.rest import Client

from app.config import settings


def send_email_alert(to_email: str, subject: str, body: str) -> None:
    if not settings.enable_email_alerts:
        return
    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password, settings.smtp_from]):
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as s:
        s.starttls()
        s.login(settings.smtp_user, settings.smtp_password)
        s.send_message(msg)


def send_sms_alert(to_phone: str, body: str) -> None:
    if not settings.enable_sms_alerts:
        return
    if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_from_number]):
        return

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    client.messages.create(
        body=body,
        from_=settings.twilio_from_number,
        to=to_phone,
    )
