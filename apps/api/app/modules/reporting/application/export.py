import json

from app.modules.commitments.application.use_cases import present
from app.shared.context import now
from app.shared.errors import DomainError
from app.shared.ports import UnitOfWork

MAX_EXPORT_ROWS = 10000
MAX_EXPORT_BYTES = 10 * 1024 * 1024


def export_workspace(uow: UnitOfWork, context):
    with uow:
        uow.consistent_read()
        contacts = uow.contacts.list(context.workspace_id, None, MAX_EXPORT_ROWS + 1, "all")[
            "items"
        ]
        commitments, _ = uow.commitments.list(context.workspace_id, None, MAX_EXPORT_ROWS + 1)
        count = len(contacts) + len(commitments)
        if count > MAX_EXPORT_ROWS:
            raise DomainError(
                "EXPORT_LIMIT_EXCEEDED", "La exportación local admite hasta 10,000 registros.", 422
            )
        transactions = uow.transactions.export_for_commitments(
            [c.id for c in commitments], MAX_EXPORT_ROWS - count + 1
        )
        if count + len(transactions) > MAX_EXPORT_ROWS:
            raise DomainError(
                "EXPORT_LIMIT_EXCEEDED", "La exportación local admite hasta 10,000 registros.", 422
            )
        workspace, _ = uow.workspaces.for_user(context.user_id)
        result = json.dumps(
            {
                "format_version": "nomi-core-0.1",
                "exported_at": now().isoformat(),
                "workspace": workspace,
                "contacts": contacts,
                "commitments": [present(c, context.timezone) for c in commitments],
                "transactions": transactions,
            },
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        if len(result) > MAX_EXPORT_BYTES:
            raise DomainError(
                "EXPORT_LIMIT_EXCEEDED", "La exportación local admite hasta 10 MB.", 422
            )
        uow.audit.record(
            context.workspace_id,
            context.user_id,
            "workspace.exported",
            "workspace",
            context.workspace_id,
        )
        uow.commit()
        return result
