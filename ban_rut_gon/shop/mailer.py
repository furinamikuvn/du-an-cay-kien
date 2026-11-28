"""
Tiện ích gửi Email cho AquaPlant Shop (hỗ trợ Resend HTTPS API và Django SMTP).
"""

import logging
import smtplib

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def is_email_delivery_configured():
    """Kiểm tra hệ thống đã sẵn sàng gửi email (Resend API, SMTP hoặc Console khi DEBUG)."""
    if getattr(settings, "RESEND_API_KEY", "").strip():
        return True
    if settings.EMAIL_BACKEND != "django.core.mail.backends.console.EmailBackend":
        return True
    return bool(settings.DEBUG)


def send_shop_email(subject, text_body, recipient_email, html_body=None):
    """
    Gửi email qua Resend HTTPS API (ưu tiên nếu có RESEND_API_KEY) hoặc Django EMAIL_BACKEND.
    Trả về True nếu gửi thành công, False nếu chưa cấu hình hoặc gửi thất bại.
    """
    resend_key = getattr(settings, "RESEND_API_KEY", "").strip()
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "AquaPlant Shop <no-reply@aquaplant.local>")

    if resend_key:
        payload = {
            "from": from_email,
            "to": [recipient_email],
            "subject": subject,
            "text": text_body,
        }
        if html_body:
            payload["html"] = html_body
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10,
            )
            if 200 <= resp.status_code < 300:
                return True
            logger.warning("Resend API returned status %s when sending password reset email.", resp.status_code)
            return False
        except requests.RequestException as exc:
            logger.warning("Resend API request failed: %s", exc.__class__.__name__)
            return False

    using_console_in_prod = (
        not settings.DEBUG and settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"
    )
    if using_console_in_prod:
        logger.warning("Email delivery skipped in production because only console backend is configured.")
        return False

    try:
        sent_count = send_mail(
            subject=subject,
            message=text_body,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_body,
            fail_silently=False,
        )
        return bool(sent_count)
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        logger.warning("SMTP/Email backend failed: %s", exc.__class__.__name__)
        return False
