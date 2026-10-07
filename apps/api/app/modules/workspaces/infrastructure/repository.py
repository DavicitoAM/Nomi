from uuid import uuid4

from sqlalchemy import select

from app.modules.workspaces.infrastructure.models import MembershipRow, WorkspaceRow
from app.shared.context import now
from app.shared.errors import DomainError


class WorkspaceRepository:
    def __init__(self, db):
        self.db = db

    def create_personal(self, user_id, name):
        workspace = WorkspaceRow(
            id=uuid4(),
            name=name,
            currency_code="MXN",
            timezone="America/Mexico_City",
            created_at=now(),
        )
        self.db.add(workspace)
        self.db.flush()
        self.db.add(
            MembershipRow(
                id=uuid4(),
                user_id=user_id,
                workspace_id=workspace.id,
                role="owner",
                created_at=now(),
            )
        )
        self.db.flush()
        return workspace.id

    def for_user(self, user_id):
        result = self.db.execute(
            select(WorkspaceRow, MembershipRow.role)
            .join(MembershipRow, MembershipRow.workspace_id == WorkspaceRow.id)
            .where(MembershipRow.user_id == user_id)
            .order_by(WorkspaceRow.created_at)
            .limit(1)
        ).first()
        if result is None:
            raise DomainError("WORKSPACE_NOT_AVAILABLE", "No tienes acceso a este espacio.", 403)
        workspace, role = result
        return {
            "id": str(workspace.id),
            "name": workspace.name,
            "currency_code": workspace.currency_code,
            "timezone": workspace.timezone,
        }, role
