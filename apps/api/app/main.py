import logging
import time
from collections import deque
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from opentelemetry import trace
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException

from app.api.routes import router
from app.core.config import settings
from app.core.database import engine
from app.shared.errors import DomainError

app = FastAPI(title="Nomi Core", version="0.1.0")
app.include_router(router)
logger = logging.getLogger("nomi.requests")
tracer = trace.get_tracer("nomi.api")
rate_lock = Lock()
attempts: dict[str, deque] = {}


def problem(request, code, detail, status):
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"urn:nomi:problem:{code.lower().replace('_', '-')}",
            "title": detail,
            "status": status,
            "detail": detail,
            "code": code,
            "instance": request.url.path,
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(DomainError)
async def domain_error(request, error):
    return problem(request, error.code, error.detail, error.status)


@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    # Never serialize Pydantic input values: these can contain passwords and financial notes.
    return problem(request, "INVALID_INPUT", "Revisa los campos y sus formatos.", 422)


@app.exception_handler(HTTPException)
async def http_error(request, error):
    return problem(request, "HTTP_ERROR", "No se pudo completar la solicitud.", error.status_code)


@app.exception_handler(IntegrityError)
async def integrity_error(request, error):
    constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", "")
    if constraint == "users_email_key":
        return problem(request, "EMAIL_ALREADY_REGISTERED", "Ese correo ya tiene una cuenta.", 409)
    return problem(
        request, "DATA_CONFLICT", "La operación entra en conflicto con los datos actuales.", 409
    )


@app.exception_handler(SQLAlchemyError)
async def database_error(request, error):
    return problem(
        request, "SERVICE_UNAVAILABLE", "No pudimos guardar. Intenta de nuevo en un momento.", 503
    )


@app.middleware("http")
async def security_and_telemetry(request: Request, call_next):
    request.state.request_id = str(uuid4())
    start = time.monotonic()
    response = None
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.headers.get("origin") != settings().app_origin:
            response = problem(request, "ORIGIN_INVALID", "Origen de solicitud no permitido.", 403)
        length = request.headers.get("content-length", "0")
        if not length.isdigit() or int(length) > 16384:
            response = problem(
                request, "REQUEST_TOO_LARGE", "La solicitud supera el límite permitido.", 413
            )
    if request.url.path in ("/api/v1/auth/register", "/api/v1/auth/login") and response is None:
        # Local, single-process limiter. Never trust a client-supplied forwarding header.
        client = request.client.host if request.client else "unknown"
        with rate_lock:
            for key in list(attempts):
                if not attempts[key] or attempts[key][-1] < start - 60:
                    del attempts[key]
            bucket = attempts.setdefault(client, deque())
            while bucket and bucket[0] < start - 60:
                bucket.popleft()
            if len(bucket) >= 20 or len(attempts) > 10000:
                response = problem(
                    request, "RATE_LIMITED", "Espera un minuto antes de volver a intentar.", 429
                )
                response.headers["Retry-After"] = "60"
            else:
                bucket.append(start)
    if response is None:
        with tracer.start_as_current_span("http.request") as span:
            try:
                response = await call_next(request)
            except Exception:
                logger.error("unhandled request_id=%s", request.state.request_id)
                response = problem(
                    request, "INTERNAL_ERROR", "Ocurrió un error. Intenta de nuevo.", 500
                )
            span.set_attribute("http.response.status_code", response.status_code)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    route = getattr(request.scope.get("route"), "path", "unmatched")
    logger.info(
        "request_id=%s route=%s status=%s duration_ms=%d",
        request.state.request_id,
        route,
        response.status_code,
        (time.monotonic() - start) * 1000,
    )
    return response


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    with engine.connect() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ready"}
