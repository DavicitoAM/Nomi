import hashlib
import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.database import session_factory
from app.modules.audit.repository import AuditRepository
from app.modules.commitments.repository import CommitmentRepository
from app.modules.contacts.repository import ContactRepository
from app.modules.identity.repository import IdentityRepository
from app.modules.transactions.repository import TransactionRepository
from app.modules.workspaces.repository import WorkspaceRepository
from app.shared.context import now
from app.shared.errors import DomainError
from app.shared.models import IdempotencyRow, OutboxRow


class EffectsRepository:
    def __init__(self, db):
        self.db = db

    def reserve(self, context, operation, key, payload):
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        request_hash = hashlib.sha256(canonical.encode()).hexdigest()
        statement = (
            insert(IdempotencyRow)
            .values(
                id=uuid4(),
                workspace_id=context.workspace_id,
                operation=operation,
                idempotency_key=key,
                request_hash=request_hash,
                created_at=now(),
            )
            .on_conflict_do_nothing(constraint="uq_idempotency")
            .returning(IdempotencyRow.id)
        )
        claimed = self.db.scalar(statement)
        row = self.db.scalar(
            select(IdempotencyRow).where(
                IdempotencyRow.workspace_id == context.workspace_id,
                IdempotencyRow.operation == operation,
                IdempotencyRow.idempotency_key == key,
            )
        )
        if row.request_hash != request_hash:
            raise DomainError(
                "IDEMPOTENCY_KEY_CONFLICT", "La clave ya corresponde a otra operación.", 409
            )
        if claimed is None and row.response is None:
            raise DomainError("OPERATION_IN_PROGRESS", "La operación sigue procesándose.", 409)
        return row.id, row.response

    def complete(self, record_id, response, resource_type, resource_id):
        from uuid import UUID

        row = self.db.get(IdempotencyRow, record_id)
        row.response = json.loads(json.dumps(response, default=str))
        row.resource_type, row.resource_id, row.http_status = (
            resource_type,
            UUID(str(resource_id)),
            201,
        )

    def emit(self, workspace_id, event, resource_id):
        self.db.add(
            OutboxRow(
                id=uuid4(),
                workspace_id=workspace_id,
                event_type=event,
                payload={"resource_id": str(resource_id)},
                occurred_at=now(),
                attempts=0,
            )
        )


class SqlUnitOfWork:
    def __init__(self, factory=session_factory):
        self.factory = factory

    def __enter__(self):
        self.db = self.factory()
        self.identity = IdentityRepository(self.db)
        self.workspaces = WorkspaceRepository(self.db)
        self.contacts = ContactRepository(self.db)
        self.commitments = CommitmentRepository(self.db)
        self.transactions = TransactionRepository(self.db)
        self.audit = AuditRepository(self.db)
        self.effects = EffectsRepository(self.db)
        return self

    def commit(self):
        self.db.commit()

    def __exit__(self, *args):
        self.db.rollback()
        self.db.close()
