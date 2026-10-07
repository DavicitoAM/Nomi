from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import Auth, Cursor, Limit
from app.api.schemas import Page
from app.modules.contacts.api.schemas import (
    ContactDetail,
    ContactEdit,
    ContactInput,
    ContactOut,
    ContactVersion,
)
from app.modules.contacts.application.use_cases import (
    archive_contact,
    create_contact,
    edit_contact,
    get_contact,
)
from app.shared.uow import SqlUnitOfWork

router = APIRouter()


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact_route(body: ContactInput, context: Auth):
    return create_contact(SqlUnitOfWork(), context, **body.model_dump())


@router.get("/contacts", response_model=Page[ContactOut])
def list_contacts(
    context: Auth,
    cursor: Cursor = None,
    limit: Limit = 30,
    status: Literal["active", "archived", "all"] = "active",
    search: Annotated[str, Query(max_length=160)] = "",
):
    with SqlUnitOfWork() as uow:
        return uow.contacts.list(context.workspace_id, cursor, limit, status, search.strip())


@router.get("/contacts/{contact_id}", response_model=ContactDetail)
def detail(contact_id: UUID, context: Auth):
    return get_contact(SqlUnitOfWork(), context, contact_id)


@router.patch("/contacts/{contact_id}", response_model=ContactOut)
def edit(contact_id: UUID, body: ContactEdit, context: Auth):
    return edit_contact(
        SqlUnitOfWork(),
        context,
        contact_id,
        body.expected_updated_at,
        body.model_dump(exclude_unset=True, exclude={"expected_updated_at"}),
    )


@router.post("/contacts/{contact_id}/archive", response_model=ContactOut)
def archive(contact_id: UUID, body: ContactVersion, context: Auth):
    return archive_contact(SqlUnitOfWork(), context, contact_id, body.expected_updated_at, True)


@router.post("/contacts/{contact_id}/restore", response_model=ContactOut)
def restore(contact_id: UUID, body: ContactVersion, context: Auth):
    return archive_contact(SqlUnitOfWork(), context, contact_id, body.expected_updated_at, False)
