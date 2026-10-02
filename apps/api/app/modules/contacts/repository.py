from uuid import uuid4

from sqlalchemy import select

from app.modules.contacts.models import ContactRow
from app.shared.context import now
from app.shared.errors import DomainError


def contact_data(row):
    return {"id": str(row.id), "name": row.name, "email": row.email, "phone": row.phone}


class ContactRepository:
    def __init__(self, db):
        self.db = db

    def create(self, workspace_id, name, email, phone):
        row = ContactRow(
            id=uuid4(),
            workspace_id=workspace_id,
            name=name,
            email=email,
            phone=phone,
            created_at=now(),
        )
        self.db.add(row)
        self.db.flush()
        return contact_data(row)

    def require_active(self, workspace_id, contact_id):
        row = self.db.scalar(
            select(ContactRow).where(
                ContactRow.id == contact_id, ContactRow.workspace_id == workspace_id
            )
        )
        if row is None:
            raise DomainError("CONTACT_NOT_FOUND", "No encontramos ese contacto.", 404)
        if row.archived_at:
            raise DomainError("CONTACT_ARCHIVED", "Restaura el contacto antes de crear pendientes.")

    def list(self, workspace_id, cursor, limit):
        query = select(ContactRow).where(
            ContactRow.workspace_id == workspace_id, ContactRow.archived_at.is_(None)
        )
        if cursor:
            query = query.where(ContactRow.id > cursor)
        rows = list(self.db.scalars(query.order_by(ContactRow.id).limit(limit + 1)))
        return {
            "items": [contact_data(r) for r in rows[:limit]],
            "next_cursor": str(rows[limit - 1].id) if len(rows) > limit else None,
        }
