import html
import json
import os
import smtplib
import ssl
import tempfile
from email.message import EmailMessage
from pathlib import Path
from uuid import UUID

from app.core.config import settings


def render_mail(event_id, message):
    purpose = message["purpose"]
    subject = {
        "verify": "Verifica tu correo en Nomi",
        "reset": "Recupera tu acceso a Nomi",
        "changed": "Tu contraseña de Nomi cambió",
    }[purpose]
    link = (
        f"{settings().app_origin.rstrip('/')}/#action={purpose}&token={message['token']}"
        if message["token"]
        else None
    )
    body = (
        (
            "Confirma la acción desde el enlace. Sólo puede utilizarse una vez. "
            f"Vence: {message['expires_at']}. Si no lo solicitaste, ignora este correo."
        )
        if link
        else (
            "Tu contraseña fue actualizada y tus sesiones anteriores se cerraron. "
            "Si no lo hiciste tú, solicita recuperar tu contraseña desde Nomi."
        )
    )
    return {
        "id": event_id,
        "recipient": message["recipient"],
        "purpose": purpose,
        "subject": subject,
        "body": body,
        "link": link,
    }


def atomic_write(path: Path, content: str):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".mail-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class MailTransport:
    def send(self, event_id, message):
        UUID(event_id)
        config = settings()
        mail = render_mail(event_id, message)
        if config.mail_backend == "file":
            if config.environment != "development":
                raise RuntimeError("Local mailbox is development-only")
            directory = config.mailbox_dir
            directory.mkdir(parents=True, exist_ok=True)
            link = (
                f'<p><a href="{html.escape(mail["link"], quote=True)}">Continuar en Nomi</a></p>'
                if mail["link"]
                else ""
            )
            document = (
                '<!doctype html><html lang="es"><meta charset="utf-8">'
                '<meta name="referrer" content="no-referrer"><title>Correo local de Nomi</title>'
                f"<h1>{html.escape(mail['subject'])}</h1><p>Para: {html.escape(mail['recipient'])}</p>"
                f"<p>{html.escape(mail['body'])}</p>{link}</html>"
            )
            atomic_write(directory / f"{event_id}.html", document)
            # Stable event filename means retries do not create another local message.
            atomic_write(directory / f"{event_id}.json", json.dumps(mail, ensure_ascii=False))
            return
        message_out = EmailMessage()
        message_out["From"] = config.smtp_from
        message_out["To"] = mail["recipient"]
        message_out["Subject"] = mail["subject"]
        message_out["Message-ID"] = f"<{event_id}@nomi.invalid>"
        message_out.set_content(mail["body"] + ("\n\n" + mail["link"] if mail["link"] else ""))
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            if config.smtp_username:
                smtp.login(
                    config.smtp_username,
                    config.smtp_password.get_secret_value() if config.smtp_password else "",
                )
            smtp.send_message(message_out)
