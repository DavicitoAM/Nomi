from uuid import uuid4

from sqlalchemy import select

from app.modules.contacts.infrastructure.models import ContactRow
from app.shared.context import now
from app.shared.errors import DomainError


def contact_data(row):
    return {
        "id": str(row.id),
        "name": row.name,
        "email": row.email,
        "phone": row.phone,
        "notes": row.notes,
        "archived_at": row.archived_at,
        "updated_at": row.updated_at,
    }


class ContactRepository:
    def __init__(self, db):
        self.db = db

    def names(self, workspace_id, ids):
        return dict(
            self.db.execute(
                select(ContactRow.id, ContactRow.name).where(
                    ContactRow.workspace_id == workspace_id, ContactRow.id.in_(ids)
                )
            ).all()
        )

    def search_ids(self, workspace_id, search):
        return list(
            self.db.scalars(
                select(ContactRow.id).where(
                    ContactRow.workspace_id == workspace_id,
                    ContactRow.name.icontains(search, autoescape=True),
                )
            )
        )

    def create(self, workspace_id, name, email, phone, notes=None):
        row = ContactRow(
            id=uuid4(),
            workspace_id=workspace_id,
            name=name,
            email=email,
            phone=phone,
            notes=notes,
            created_at=now(),
            updated_at=now(),
        )
        self.db.add(row)
        self.db.flush()
        return contact_data(row)

    def _get(self, workspace_id, contact_id, lock=False):
        query = select(ContactRow).where(
            ContactRow.id == contact_id, ContactRow.workspace_id == workspace_id
        )
        row = self.db.scalar(query.with_for_update() if lock else query)
        if row is None:
            raise DomainError("CONTACT_NOT_FOUND", "No encontramos ese contacto.", 404)
        return row

    def get(self, workspace_id, contact_id):
        return contact_data(self._get(workspace_id, contact_id))

    def edit(self, workspace_id, contact_id, expected_updated_at, changes):
        row = self._get(workspace_id, contact_id, lock=True)
        if row.updated_at != expected_updated_at:
            raise DomainError("VERSION_CONFLICT", "El contacto cambió. Actualiza y revisa.", 409)
        for field, value in changes.items():
            setattr(row, field, value)
        row.updated_at = now()
        self.db.flush()
        return contact_data(row)

    def archive(self, workspace_id, contact_id, expected_updated_at, archived):
        row = self._get(workspace_id, contact_id, lock=True)
        if bool(row.archived_at) == archived:
            return contact_data(row), False
        if row.updated_at != expected_updated_at:
            raise DomainError("VERSION_CONFLICT", "El contacto cambió. Actualiza y revisa.", 409)
        row.updated_at = now()
        row.archived_at = row.updated_at if archived else None
        self.db.flush()
        return contact_data(row), True

    def require_active(self, workspace_id, contact_id):
        row = self.db.scalar(
            select(ContactRow)
            .where(ContactRow.id == contact_id, ContactRow.workspace_id == workspace_id)
            .with_for_update()
        )
        if row is None:
            raise DomainError("CONTACT_NOT_FOUND", "No encontramos ese contacto.", 404)
        if row.archived_at:
            raise DomainError("CONTACT_ARCHIVED", "Restaura el contacto antes de crear pendientes.")

    def list(self, workspace_id, cursor, limit, status="active", search=""):
        query = select(ContactRow).where(ContactRow.workspace_id == workspace_id)
        if status != "all":
            query = query.where(
                ContactRow.archived_at.is_(None)
                if status == "active"
                else ContactRow.archived_at.is_not(None)
            )
        if search:
            query = query.where(ContactRow.name.icontains(search, autoescape=True))
        if cursor:
            query = query.where(ContactRow.id > cursor)
        rows = list(self.db.scalars(query.order_by(ContactRow.id).limit(limit + 1)))
        return {
            "items": [contact_data(r) for r in rows[:limit]],
            "next_cursor": str(rows[limit - 1].id) if len(rows) > limit else None,
        }
