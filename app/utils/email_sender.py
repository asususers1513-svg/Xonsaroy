import os
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from typing import List, Optional

def send_email(
    subject: str,
    body: str,
    to: List[str],
    *,
    html_body: Optional[str] = None,
    attachments: Optional[List[tuple]] = None,
) -> bool:
    """Send an email using the SMTP configuration defined in Django settings.

    Returns True on success, False on failure.
    """
    try:
        connection = get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=getattr(settings, "EMAIL_USE_SSL", False),
        )
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to,
            connection=connection,
        )
        if html_body:
            email.content_subtype = "html"
            email.body = html_body
        if attachments:
            for attachment in attachments:
                # attachment = (filename, content, mimetype)
                email.attach(*attachment)
        email.send(fail_silently=False)
        return True
    except Exception as e:
        # In a real project replace print with proper logging
        print(f"[Email Error] {e}")
        return False
