from __future__ import annotations

from app.services.notifier import send_email_alert, send_sms_alert


def notify_recipients(db, person, candidate) -> int:
    sent = 0
    for recipient in person.alert_recipients:
        if (
            (candidate.risk_score or 0.0) < (recipient.min_risk_threshold or 0.70)
            and (candidate.viral_score or 0.0) < (recipient.min_viral_threshold or 0.60)
        ):
            continue

        subject = f"[Deepfake Alert] {person.full_name} - {candidate.platform} - {candidate.risk_label}"
        body = (
            f"Target: {person.full_name}\n"
            f"Platform: {candidate.platform}\n"
            f"URL: {candidate.url}\n"
            f"Account: {candidate.account_name}\n"
            f"Risk: {candidate.risk_score:.2f} ({candidate.risk_label})\n"
            f"Virality: {(candidate.viral_score or 0.0):.2f}\n"
            f"Face match: {candidate.face_match_score}\n"
            f"Voice match: {candidate.voice_match_score}\n"
            f"Discovery reason: {candidate.discovery_reason}\n"
        )

        if recipient.send_email and recipient.email:
            send_email_alert(recipient.email, subject, body)
            sent += 1

        if recipient.send_sms and recipient.phone_e164:
            send_sms_alert(
                recipient.phone_e164,
                f"{person.full_name}: {candidate.platform} {candidate.risk_label} "
                f"risk={candidate.risk_score:.2f} viral={(candidate.viral_score or 0.0):.2f} {candidate.url}",
            )
            sent += 1

    return sent
