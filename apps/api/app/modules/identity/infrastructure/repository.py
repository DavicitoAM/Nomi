import hashlib
from datetime import timedelta
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import delete, func, or_, select, update

from app.modules.identity.infrastructure.models import (
    EmailVerificationTokenRow,
    PasswordResetTokenRow,
    SessionRow,
    UserRow,
)
from app.modules.identity.infrastructure.token_cipher import delivery_cipher
from app.shared.context import now
from app.shared.errors import DomainError

TOKEN_MODELS = {"verify": EmailVerificationTokenRow, "reset": PasswordResetTokenRow}


def digest(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


class IdentityRepository:
    def __init__(self, db):
        self.db = db

    def cleanup_expired(self, apply=False):
        instant = now()
        rules = [
            (
                SessionRow,
                or_(
                    SessionRow.expires_at < instant - timedelta(days=30),
                    SessionRow.revoked_at < instant - timedelta(days=30),
                ),
            )
        ]
        rules.extend(
            (model, model.expires_at < instant - timedelta(days=7))
            for model in TOKEN_MODELS.values()
        )
        result = {}
        for model, predicate in rules:
            eligible = self.db.scalar(select(func.count()).select_from(model).where(predicate))
            removed = 0
            if apply:
                ids = list(
                    self.db.scalars(
                        select(model.id)
                        .where(predicate)
                        .order_by(model.id)
                        .limit(1000)
                        .with_for_update(skip_locked=True)
                    )
                )
                if ids:
                    removed = self.db.execute(delete(model).where(model.id.in_(ids))).rowcount
            result[model.__tablename__] = {"eligible": eligible, "removed": removed}
        return result

    def create_user(self, email, password_hash, display_name):
        user = UserRow(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            status="pending_verification",
            created_at=now(),
            updated_at=now(),
        )
        self.db.add(user)
        self.db.flush()
        return user.id

    def credentials(self, email):
        user = self.db.scalar(select(UserRow).where(UserRow.email == email).with_for_update())
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

    def user_id_for_email(self, email):
        return self.db.scalar(select(UserRow.id).where(UserRow.email == email))

    def issue_token(self, user_id, purpose, cooldown=True):
        user = self.db.scalar(select(UserRow).where(UserRow.id == user_id).with_for_update())
        if user is None or user.status not in ("active", "pending_verification"):
            return None
        if purpose == "verify" and user.status != "pending_verification":
            return None
        model = TOKEN_MODELS[purpose]
        instant = now()
        recent = self.db.scalar(
            select(model.id)
            .where(model.user_id == user_id, model.created_at > instant - timedelta(seconds=60))
            .limit(1)
        )
        if cooldown and recent:
            return None
        self.db.execute(
            update(model)
            .where(model.user_id == user_id, model.used_at.is_(None))
            .values(used_at=instant, delivery_secret=None)
        )
        token = token_urlsafe(32)
        row = model(
            id=uuid4(),
            user_id=user_id,
            token_hash=digest(token),
            delivery_secret=delivery_cipher().encrypt(token.encode()).decode(),
            created_at=instant,
            expires_at=instant + timedelta(minutes=30 if purpose == "reset" else 1440),
        )
        self.db.add(row)
        self.db.flush()
        return row.id

    def consume_token(self, token, purpose, password_hash=None):
        model = TOKEN_MODELS[purpose]
        # Lock user before token everywhere to serialize reset, resend and login consistently.
        user_id = self.db.scalar(select(model.user_id).where(model.token_hash == digest(token)))
        user = (
            self.db.scalar(select(UserRow).where(UserRow.id == user_id).with_for_update())
            if user_id
            else None
        )
        row = (
            self.db.scalar(
                select(model)
                .where(
                    model.token_hash == digest(token),
                    model.used_at.is_(None),
                    model.expires_at > now(),
                )
                .with_for_update()
            )
            if user
            else None
        )
        if row is None or user.status not in ("active", "pending_verification"):
            raise DomainError(
                "ACCOUNT_LINK_INVALID",
                "El enlace venció o ya fue utilizado. Solicita uno nuevo.",
                400,
            )
        instant = now()
        if purpose == "verify":
            user.status, user.email_verified_at = "active", instant
        else:
            user.password_hash = password_hash
            self.db.execute(
                update(SessionRow)
                .where(SessionRow.user_id == user_id, SessionRow.revoked_at.is_(None))
                .values(revoked_at=instant)
            )
        user.updated_at = instant
        for target in TOKEN_MODELS.values() if purpose == "reset" else (model,):
            self.db.execute(
                update(target)
                .where(target.user_id == user_id, target.used_at.is_(None))
                .values(used_at=instant, delivery_secret=None)
            )
        return user_id

    def resolve_mail_resource(self, resource_id, purpose):
        model = TOKEN_MODELS[purpose]
        if self.db.get(model, resource_id):
            return resource_id
        # Pre-migration registration events referenced User; prepare a durable token once.
        if purpose == "verify":
            if self.db.scalar(select(model.id).where(model.user_id == resource_id).limit(1)):
                return None
            return self.issue_token(resource_id, purpose)
        return None

    def mail_data(self, token_id, purpose):
        row = self.db.get(TOKEN_MODELS[purpose], token_id)
        if not row or row.used_at or row.expires_at <= now() or not row.delivery_secret:
            return None
        user = self.db.get(UserRow, row.user_id)
        if user.status not in ("active", "pending_verification") or (
            purpose == "verify" and user.status != "pending_verification"
        ):
            return None
        return {
            "recipient": user.email,
            "token": delivery_cipher().decrypt(row.delivery_secret.encode()).decode(),
            "expires_at": row.expires_at.isoformat(),
            "purpose": purpose,
        }

    def clear_delivery_secret(self, token_id, purpose):
        model = TOKEN_MODELS[purpose]
        self.db.execute(update(model).where(model.id == token_id).values(delivery_secret=None))

    def clear_expired_delivery_secrets(self):
        for model in TOKEN_MODELS.values():
            self.db.execute(
                update(model)
                .where(model.expires_at <= now(), model.delivery_secret.is_not(None))
                .values(delivery_secret=None)
            )
