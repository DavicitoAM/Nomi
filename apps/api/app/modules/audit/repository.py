from uuid import UUID, uuid4

from app.modules.audit.models import AuditRow
from app.shared.context import now


class AuditRepository:
    def __init__(self, db):
        self.db = db

    def record(self, workspace_id, user_id, action, entity_type, entity_id):
        self.db.add(
            AuditRow(
                id=uuid4(),
                workspace_id=workspace_id,
                actor_user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=UUID(str(entity_id)),
                details={},
                created_at=now(),
            )
        )
        self.db.flush()
