from secrets import compare_digest
from typing import Annotated
from uuid import UUID

from fastapi import Request, Security
from fastapi.security import APIKeyCookie

from app.modules.identity.repository import digest
from app.shared.context import Context
from app.shared.errors import DomainError
from app.shared.uow import SqlUnitOfWork

session_cookie = APIKeyCookie(name="nomi_session", auto_error=False)


def auth_context(
    request: Request, token: Annotated[str | None, Security(session_cookie)]
) -> Context:
    if not token:
        raise DomainError("UNAUTHENTICATED", "Inicia sesión para continuar.", 401)
    with SqlUnitOfWork() as uow:
        session = uow.identity.session(token)
        if session is None:
            raise DomainError("UNAUTHENTICATED", "Tu sesión terminó. Vuelve a entrar.", 401)
        session_id, user_id, csrf_hash = session
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            csrf = request.headers.get("X-CSRF-Token", "")
            if not csrf or not compare_digest(digest(csrf), csrf_hash):
                raise DomainError("CSRF_INVALID", "Actualiza la página para continuar.", 403)
        workspace, role = uow.workspaces.for_user(user_id)
        if role != "owner":
            raise DomainError("FORBIDDEN", "Esta versión sólo permite operar al propietario.", 403)
        return Context(
            user_id,
            UUID(workspace["id"]),
            workspace["currency_code"],
            workspace["timezone"],
            session_id,
        )
