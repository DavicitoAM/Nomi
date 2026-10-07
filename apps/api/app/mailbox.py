"""Loopback-only development mailbox. No real mail is sent by this viewer."""

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import UUID

from app.core.config import settings


class MailboxHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Host") not in ("localhost:8025", "127.0.0.1:8025"):
            self.send_error(403)
            return
        directory = settings().mailbox_dir
        title = "Buzón local de Nomi"
        if self.path == "/":
            files = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[
                :100
            ]
            body = "<p>Desarrollo: estos mensajes no se enviaron a un proveedor externo.</p><p><a href='/'>Actualizar buzón</a></p><ul>"
            for path in files:
                mail = json.loads(path.read_text(encoding="utf-8"))
                body += f'<li><a href="/message/{path.stem}">{html.escape(mail["subject"])}</a> — {html.escape(mail["recipient"])}</li>'
            body += "</ul>"
        else:
            try:
                if not self.path.startswith("/message/"):
                    raise ValueError()
                message_id = UUID(self.path.removeprefix("/message/"))
                mail = json.loads((directory / f"{message_id}.json").read_text(encoding="utf-8"))
            except (ValueError, OSError):
                self.send_error(404)
                return
            title = mail["subject"]
            body = (
                f"<p>Para: {html.escape(mail['recipient'])}</p><p>{html.escape(mail['body'])}</p>"
            )
            if mail["link"]:
                body += f'<p><a href="{html.escape(mail["link"], quote=True)}">Continuar en Nomi</a></p>'
            body += "<p><a href='/'>Volver al buzón</a></p>"
        encoded = (
            f'<!doctype html><html lang="es"><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f"<h1>{html.escape(title)}</h1>{body}</html>"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_):
        pass


def main():
    config = settings()
    if config.environment != "development" or config.mail_backend != "file":
        raise SystemExit("The mailbox viewer requires development and MAIL_BACKEND=file")
    print("Local mailbox: http://localhost:8025", flush=True)
    try:
        ThreadingHTTPServer(("127.0.0.1", 8025), MailboxHandler).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
