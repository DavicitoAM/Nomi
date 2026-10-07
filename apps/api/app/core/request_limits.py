"""Bound actual request bytes before parsing or dispatching a mutation."""

import asyncio
from uuid import uuid4

from starlette.responses import JSONResponse


class RequestLimits:
    def __init__(self, app, max_bytes=16384, timeout=10):
        self.app, self.max_bytes, self.timeout = app, max_bytes, timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in ("POST", "PUT", "PATCH", "DELETE"):
            return await self.app(scope, receive, send)

        async def reject(status, code, detail):
            request_id = str(uuid4())
            response = JSONResponse(
                {
                    "type": f"urn:nomi:problem:{code.lower().replace('_', '-')}",
                    "title": detail,
                    "detail": detail,
                    "status": status,
                    "code": code,
                    "instance": scope["path"],
                    "request_id": request_id,
                },
                status_code=status,
                media_type="application/problem+json",
                headers={
                    "X-Request-ID": request_id,
                    "Cache-Control": "no-store",
                    "X-Content-Type-Options": "nosniff",
                },
            )
            await response(scope, receive, send)

        lengths = [value for name, value in scope["headers"] if name.lower() == b"content-length"]
        if len(lengths) > 1 or (lengths and not lengths[0].isdigit()):
            return await reject(400, "INVALID_CONTENT_LENGTH", "Tamaño de solicitud inválido.")
        if lengths and (len(lengths[0]) > 10 or int(lengths[0]) > self.max_bytes):
            return await reject(
                413, "REQUEST_TOO_LARGE", "La solicitud supera el límite permitido."
            )
        if any(
            name.lower() == b"content-encoding" and value.lower() != b"identity"
            for name, value in scope["headers"]
        ):
            return await reject(415, "UNSUPPORTED_ENCODING", "Envía JSON sin compresión.")
        body = bytearray()
        try:
            async with asyncio.timeout(self.timeout):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    if len(body) + len(chunk) > self.max_bytes:
                        return await reject(
                            413, "REQUEST_TOO_LARGE", "La solicitud supera el límite permitido."
                        )
                    body.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await reject(
                408, "REQUEST_TIMEOUT", "Se agotó el tiempo para recibir la solicitud."
            )
        if lengths and int(lengths[0]) != len(body):
            return await reject(400, "INVALID_CONTENT_LENGTH", "Tamaño de solicitud inválido.")
        consumed = False

        async def replay():
            nonlocal consumed
            if consumed:
                return await receive()
            consumed = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay, send)
