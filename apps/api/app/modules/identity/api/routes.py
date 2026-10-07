import asyncio
import time

from fastapi import APIRouter, Response
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import Auth
from app.core.config import settings
from app.modules.identity.api.schemas import (
    EmailInput,
    LoginInput,
    MessageOut,
    ProfileOut,
    RegisterInput,
    ResetPasswordInput,
    TokenInput,
)
from app.modules.identity.application.use_cases import (
    login,
    register,
    request_account_link,
    reset_password,
    verify_email,
)
from app.shared.uow import SqlUnitOfWork

router = APIRouter()


@router.post("/auth/password/forgot", response_model=MessageOut, status_code=202)
async def forgot(body: EmailInput):
    started = time.monotonic()
    await run_in_threadpool(request_account_link, SqlUnitOfWork(), "reset", email=str(body.email))
    await asyncio.sleep(max(0, 0.25 - (time.monotonic() - started)))
    return {"message": "Si la cuenta puede recuperarse, recibirás un enlace. Revisa tu correo."}


@router.post("/auth/password/reset", response_model=MessageOut)
def reset(body: ResetPasswordInput, response: Response):
    reset_password(SqlUnitOfWork(), body.token, body.password)
    response.delete_cookie("nomi_session", path="/")
    response.delete_cookie("nomi_csrf", path="/")
    return {"message": "Contraseña actualizada. Inicia sesión de nuevo en tus dispositivos."}


@router.post("/auth/email/verify", response_model=MessageOut)
def verify(body: TokenInput):
    verify_email(SqlUnitOfWork(), body.token)
    return {"message": "Correo verificado. Ya puedes acceder a tu espacio."}


@router.post("/auth/email/resend", response_model=MessageOut, status_code=202)
def resend(context: Auth):
    request_account_link(SqlUnitOfWork(), "verify", user_id=context.user_id)
    return {
        "message": "Si tu correo necesita verificación, recibirás un enlace. Espera un minuto entre solicitudes."
    }


def set_session(response, result):
    profile, token, csrf = result
    profile["can_operate"] = (
        settings().environment == "development" or profile["user"]["email_verified"]
    )
    options = dict(
        secure=settings().cookie_secure,
        samesite="lax",
        path="/",
        max_age=settings().session_hours * 3600,
    )
    response.set_cookie("nomi_session", token, httponly=True, **options)
    response.set_cookie("nomi_csrf", csrf, httponly=False, **options)
    return profile


@router.post("/auth/register", response_model=ProfileOut, status_code=201)
def register_route(body: RegisterInput, response: Response):
    return set_session(
        response,
        register(SqlUnitOfWork(), **body.model_dump(), session_hours=settings().session_hours),
    )


@router.post("/auth/login", response_model=ProfileOut)
def login_route(body: LoginInput, response: Response):
    return set_session(
        response,
        login(SqlUnitOfWork(), **body.model_dump(), session_hours=settings().session_hours),
    )


@router.post("/auth/logout", status_code=204)
def logout_route(context: Auth):
    with SqlUnitOfWork() as uow:
        uow.identity.revoke(context.session_id)
        uow.commit()
    response = Response(status_code=204)
    response.delete_cookie("nomi_session", path="/")
    response.delete_cookie("nomi_csrf", path="/")
    return response


@router.get("/me", response_model=ProfileOut)
def me(context: Auth):
    with SqlUnitOfWork() as uow:
        workspace, role = uow.workspaces.for_user(context.user_id)
        user = uow.identity.profile(context.user_id)
        return {
            "user": user,
            "workspace": workspace,
            "membership": {"role": role},
            "can_operate": settings().environment == "development" or user["email_verified"],
        }
