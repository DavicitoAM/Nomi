import hashlib
import json
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.core.database import session_factory
from app.modules.audit.infrastructure.repository import AuditRepository
from app.modules.commitments.infrastructure.repository import CommitmentRepository
from app.modules.contacts.infrastructure.repository import ContactRepository
from app.modules.identity.infrastructure.repository import IdentityRepository
from app.modules.transactions.infrastructure.repository import TransactionRepository
from app.modules.workspaces.infrastructure.repository import WorkspaceRepository
from app.shared.context import now
from app.shared.errors import DomainError
from app.shared.models import IdempotencyRow, OutboxRow


class EffectsRepository:
    def __init__(self, db):
        self.db = db

    def reserve(self, context, operation, key, payload, *, compatible_payloads=()):
        def digest(value):
            canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
            return hashlib.sha256(canonical.encode()).hexdigest()

        request_hash = digest(payload)
        accepted_hashes = {request_hash, *(digest(value) for value in compatible_payloads)}
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
        if row.request_hash not in accepted_hashes:
            raise DomainError(
                "IDEMPOTENCY_KEY_CONFLICT", "La clave ya corresponde a otra operación.", 409
            )
        if claimed is None and row.response is None:
            raise DomainError("OPERATION_IN_PROGRESS", "La operación sigue procesándose.", 409)
        return row.id, row.response

    def complete(self, record_id, response, resource_type, resource_id, status=201):
        from uuid import UUID

        row = self.db.get(IdempotencyRow, record_id)
        row.response = json.loads(json.dumps(response, default=str))
        row.resource_type, row.resource_id, row.http_status = (
            resource_type,
            UUID(str(resource_id)),
            status,
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

    def claim_mail(self):
        row = self.db.scalar(
            select(OutboxRow)
            .where(
                OutboxRow.event_type.in_(
                    ["EmailVerificationRequested", "PasswordResetRequested", "PasswordChanged"]
                ),
                OutboxRow.processed_at.is_(None),
                OutboxRow.available_at <= now(),
                OutboxRow.attempts < 8,
            )
            .order_by(OutboxRow.occurred_at, OutboxRow.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if row is None:
            return None
        row.attempts += 1
        row.available_at = now() + timedelta(seconds=60)
        return {
            "id": row.id,
            "attempts": row.attempts,
            "event_type": row.event_type,
            "resource_id": row.payload["resource_id"],
        }

    def prepare_mail_resource(self, event_id, attempt, resource_id):
        self.db.execute(
            update(OutboxRow)
            .where(
                OutboxRow.id == event_id,
                OutboxRow.attempts == attempt,
                OutboxRow.processed_at.is_(None),
            )
            .values(payload={"resource_id": str(resource_id)})
        )

    def finish_mail(self, event_id, attempt, error=None):
        values = {"last_error_code": error}
        if error:
            values["available_at"] = now() + timedelta(seconds=min(3600, 2**attempt))
        else:
            values["processed_at"] = now()
        result = self.db.execute(
            update(OutboxRow)
            .where(
                OutboxRow.id == event_id,
                OutboxRow.attempts == attempt,
                OutboxRow.processed_at.is_(None),
            )
            .values(**values)
        )
        return result.rowcount == 1


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

    def consistent_read(self):
        self.db.connection(execution_options={"isolation_level": "REPEATABLE READ"})

    def __exit__(self, *args):
        self.db.rollback()
        self.db.close()
