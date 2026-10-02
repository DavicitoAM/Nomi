from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response

from app.api.schemas import (
    CommitmentInput,
    CommitmentOut,
    ContactInput,
    ContactOut,
    DashboardOut,
    LoginInput,
    Page,
    PaymentInput,
    PaymentOut,
    Problem,
    ProfileOut,
    RegisterInput,
    TransactionOut,
)
from app.api.security import auth_context
from app.core.config import settings
from app.modules.commitments.application import create_commitment, present
from app.modules.contacts.application import create_contact
from app.modules.identity.application import login, register
from app.modules.reporting.application import get_dashboard
from app.modules.transactions.application import register_payment
from app.shared.context import Context
from app.shared.uow import SqlUnitOfWork

router = APIRouter(
    prefix="/api/v1",
    responses={
        status: {
            "model": Problem,
            "description": "Problem Details",
            "content": {"application/problem+json": {}},
        }
        for status in (400, 401, 403, 404, 409, 422, 429, 503)
    },
)
Auth = Annotated[Context, Depends(auth_context)]
Key = Annotated[UUID, Header(alias="Idempotency-Key")]
Cursor = Annotated[UUID | None, Query()]
Limit = Annotated[int, Query(ge=1, le=100)]


def set_session(response, result):
    profile, token, csrf = result
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
        return {
            "user": uow.identity.profile(context.user_id),
            "workspace": workspace,
            "membership": {"role": role},
        }


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact_route(body: ContactInput, context: Auth):
    return create_contact(SqlUnitOfWork(), context, **body.model_dump())


@router.get("/contacts", response_model=Page[ContactOut])
def list_contacts(context: Auth, cursor: Cursor = None, limit: Limit = 30):
    with SqlUnitOfWork() as uow:
        return uow.contacts.list(context.workspace_id, cursor, limit)


@router.post("/commitments", response_model=CommitmentOut, status_code=201)
def create_commitment_route(body: CommitmentInput, context: Auth, key: Key):
    return create_commitment(SqlUnitOfWork(), context, key, **body.model_dump())


@router.get("/commitments", response_model=Page[CommitmentOut])
def list_commitments(context: Auth, cursor: Cursor = None, limit: Limit = 30):
    with SqlUnitOfWork() as uow:
        rows, next_cursor = uow.commitments.list(context.workspace_id, cursor, limit)
        return {
            "items": [present(row, context.timezone) for row in rows],
            "next_cursor": next_cursor,
        }


@router.get("/commitments/{commitment_id}", response_model=CommitmentOut)
def get_commitment(commitment_id: UUID, context: Auth):
    with SqlUnitOfWork() as uow:
        return present(uow.commitments.get(context.workspace_id, commitment_id), context.timezone)


@router.post(
    "/commitments/{commitment_id}/transactions", response_model=PaymentOut, status_code=201
)
def pay(commitment_id: UUID, body: PaymentInput, context: Auth, key: Key):
    return register_payment(SqlUnitOfWork(), context, key, commitment_id, **body.model_dump())


@router.get("/commitments/{commitment_id}/transactions", response_model=Page[TransactionOut])
def history(commitment_id: UUID, context: Auth, cursor: Cursor = None, limit: Limit = 30):
    with SqlUnitOfWork() as uow:
        commitment = uow.commitments.get(context.workspace_id, commitment_id)
        return uow.transactions.history(commitment, cursor, limit)


@router.get("/dashboard/summary", response_model=DashboardOut)
def dashboard(context: Auth):
    return get_dashboard(SqlUnitOfWork(), context)
