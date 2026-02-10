import os
import logging

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


def send_password_reset_email(to_email: str, reset_token: str, user_name: str) -> bool:
    """
    Envia email de recuperacao de senha via SendGrid.
    Degradacao graciosa: se SENDGRID_API_KEY nao configurada, loga token e retorna True.
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    if not SENDGRID_API_KEY:
        logger.warning(
            f"SendGrid nao configurado. Token de reset para {to_email}: {reset_token}"
        )
        logger.warning(f"Link de reset: {reset_link}")
        return True

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject="Meu Controle - Recuperacao de Senha",
            html_content=f"""
            <h2>Recuperacao de Senha</h2>
            <p>Ola {user_name},</p>
            <p>Voce solicitou a recuperacao de senha. Clique no link abaixo para redefinir:</p>
            <p><a href="{reset_link}">Redefinir minha senha</a></p>
            <p>Este link expira em 1 hora.</p>
            <p>Se voce nao solicitou esta recuperacao, ignore este email.</p>
            """,
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar email via SendGrid: {e}")
        return False
