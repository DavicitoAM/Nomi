from datetime import timedelta
from secrets import token_urlsafe
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.shared.context import now
from app.shared.errors import DomainError
from app.shared.ports import UnitOfWork

hasher = PasswordHasher()
# Equal-cost password check for unknown users. No user secret is embedded here.
dummy_hash = hasher.hash(token_urlsafe(32))


def establish_session(uow, user_id, session_hours):
    token, csrf = token_urlsafe(32), token_urlsafe(32)
    uow.identity.create_session(user_id, token, csrf, now() + timedelta(hours=session_hours))
    workspace, role = uow.workspaces.for_user(user_id)
    profile = {
        "user": uow.identity.profile(user_id),
        "workspace": workspace,
        "membership": {"role": role},
    }
    return profile, token, csrf


def register(uow: UnitOfWork, email: str, password: str, display_name: str, session_hours: int):
    password_hash = hasher.hash(password)
    with uow:
        if uow.identity.credentials(email):
            raise DomainError("EMAIL_ALREADY_REGISTERED", "Ese correo ya tiene una cuenta.", 409)
        user_id = uow.identity.create_user(email, password_hash, display_name)
        workspace_id = uow.workspaces.create_personal(user_id, "Mi espacio")
        uow.audit.record(workspace_id, user_id, "user.registered", "user", user_id)
        token_id = uow.identity.issue_token(user_id, "verify")
        uow.effects.emit(workspace_id, "EmailVerificationRequested", token_id)
        result = establish_session(uow, user_id, session_hours)
        uow.commit()
        return result


def login(uow: UnitOfWork, email: str, password: str, session_hours: int):
    with uow:
        credentials = uow.identity.credentials(email)
        try:
            hasher.verify(credentials[1] if credentials else dummy_hash, password)
        except VerifyMismatchError:
            raise DomainError(
                "INVALID_CREDENTIALS", "Correo o contraseña incorrectos.", 401
            ) from None
        if credentials is None or credentials[2] not in ("active", "pending_verification"):
            raise DomainError("INVALID_CREDENTIALS", "Correo o contraseña incorrectos.", 401)
        result = establish_session(uow, credentials[0], session_hours)
        uow.audit.record(
            UUID(result[0]["workspace"]["id"]),
            credentials[0],
            "user.logged_in",
            "user",
            credentials[0],
        )
        uow.commit()
        return result


def request_account_link(uow: UnitOfWork, purpose: str, *, email=None, user_id=None):
    with uow:
        user_id = user_id or uow.identity.user_id_for_email(email)
        if user_id is None:
            return
        token_id = uow.identity.issue_token(user_id, purpose)
        if token_id is None:
            return
        workspace, _ = uow.workspaces.for_user(user_id)
        workspace_id = UUID(workspace["id"])
        uow.audit.record(workspace_id, user_id, f"user.{purpose}_requested", "user", user_id)
        event = "EmailVerificationRequested" if purpose == "verify" else "PasswordResetRequested"
        uow.effects.emit(workspace_id, event, token_id)
        uow.commit()


def verify_email(uow: UnitOfWork, token: str):
    with uow:
        user_id = uow.identity.consume_token(token, "verify")
        workspace, _ = uow.workspaces.for_user(user_id)
        uow.audit.record(UUID(workspace["id"]), user_id, "user.email_verified", "user", user_id)
        uow.commit()


def reset_password(uow: UnitOfWork, token: str, password: str):
    password_hash = hasher.hash(password)
    with uow:
        user_id = uow.identity.consume_token(token, "reset", password_hash)
        workspace, _ = uow.workspaces.for_user(user_id)
        uow.audit.record(UUID(workspace["id"]), user_id, "user.password_reset", "user", user_id)
        uow.effects.emit(UUID(workspace["id"]), "PasswordChanged", user_id)
        uow.commit()
