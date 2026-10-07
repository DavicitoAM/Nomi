from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import Auth, Cursor, Key, Limit
from app.api.schemas import Page
from app.modules.commitments.api.schemas import (
    CommitmentEdit,
    CommitmentInput,
    CommitmentListOut,
    CommitmentOut,
    CommitmentVersion,
)
from app.modules.commitments.application.use_cases import (
    create_commitment,
    list_commitments,
    present,
    revise_commitment,
)
from app.shared.uow import SqlUnitOfWork

router = APIRouter()


@router.post("/commitments", response_model=CommitmentOut, status_code=201)
def create_commitment_route(body: CommitmentInput, context: Auth, key: Key):
    return create_commitment(SqlUnitOfWork(), context, key, **body.model_dump())


@router.get("/commitments", response_model=Page[CommitmentListOut])
def list_commitments_route(
    context: Auth,
    cursor: Cursor = None,
    limit: Limit = 30,
    filter: Literal["all", "receivable", "payable", "overdue", "due_soon"] = "all",
    search: Annotated[str, Query(max_length=160)] = "",
):
    return list_commitments(SqlUnitOfWork(), context, cursor, limit, filter, search.strip())


@router.get("/commitments/{commitment_id}", response_model=CommitmentOut)
def get_commitment(commitment_id: UUID, context: Auth):
    with SqlUnitOfWork() as uow:
        return present(uow.commitments.get(context.workspace_id, commitment_id), context.timezone)


@router.patch("/commitments/{commitment_id}", response_model=CommitmentOut)
def edit_commitment(commitment_id: UUID, body: CommitmentEdit, context: Auth):
    return revise_commitment(
        SqlUnitOfWork(),
        context,
        commitment_id,
        body.expected_version,
        changes=body.model_dump(exclude_unset=True, exclude={"expected_version"}),
    )


@router.post("/commitments/{commitment_id}/cancel", response_model=CommitmentOut)
def cancel_commitment(commitment_id: UUID, body: CommitmentVersion, context: Auth, key: Key):
    return revise_commitment(
        SqlUnitOfWork(), context, commitment_id, body.expected_version, cancel=True, key=key
    )
