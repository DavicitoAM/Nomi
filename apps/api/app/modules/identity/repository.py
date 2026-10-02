import hashlib
from uuid import uuid4

from sqlalchemy import select, update

from app.modules.identity.models import SessionRow, UserRow
from app.shared.context import now


def digest(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


class IdentityRepository:
    def __init__(self, db):
        self.db = db

    def create_user(self, email, password_hash, display_name):
        user = UserRow(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            status="pending_verification",
            created_at=now(),
        )
        self.db.add(user)
        self.db.flush()
        return user.id

    def credentials(self, email):
        user = self.db.scalar(select(UserRow).where(UserRow.email == email))
        return None if user is None else (user.id, user.password_hash, user.status)

    def profile(self, user_id):
        user = self.db.get(UserRow, user_id)
        return {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "email_verified": user.status == "active",
        }

    def create_session(self, user_id, token, csrf, expires):
        row = SessionRow(
            id=uuid4(),
            user_id=user_id,
            token_hash=digest(token),
            csrf_hash=digest(csrf),
            created_at=now(),
            expires_at=expires,
        )
        self.db.add(row)

    def session(self, token):
        row = self.db.execute(
            select(SessionRow, UserRow.status)
            .join(UserRow)
            .where(
                SessionRow.token_hash == digest(token),
                SessionRow.revoked_at.is_(None),
                SessionRow.expires_at > now(),
                UserRow.status.in_(["active", "pending_verification"]),
            )
        ).first()
        return None if row is None else (row[0].id, row[0].user_id, row[0].csrf_hash)

    def revoke(self, session_id):
        self.db.execute(
            update(SessionRow).where(SessionRow.id == session_id).values(revoked_at=now())
        )
