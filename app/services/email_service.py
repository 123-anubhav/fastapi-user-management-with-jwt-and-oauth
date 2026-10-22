import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    # For local development, log the token instead of sending email.
    # Never return reset tokens in API responses in production.
    reset_link = f"{settings.frontend_reset_url}?token={reset_token}"
    if not settings.smtp_host or not settings.smtp_from_email:
        print(f"[LOCAL ONLY] Password reset link for {to_email}: {reset_link}")
        return False

    message = EmailMessage()
    message["Subject"] = "Reset your password"
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message.set_content(f"Use this link to reset your password (expires soon):\n{reset_link}")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
    return True
