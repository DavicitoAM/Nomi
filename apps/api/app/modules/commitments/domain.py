from dataclasses import dataclass, replace
from datetime import date
from uuid import UUID

from app.shared.errors import DomainError

MAX_MONEY = 9_000_000_000_000  # minor units; safely representable by the web client


@dataclass(frozen=True)
class Commitment:
    id: UUID
    workspace_id: UUID
    contact_id: UUID
    direction: str
    original_amount_minor: int
    balance_minor: int
    currency_code: str
    concept: str | None
    due_date: date | None
    lifecycle_status: str = "open"
    version: int = 1

    @property
    def payment_state(self) -> str:
        if self.balance_minor == 0:
            return "paid"
        return "pending" if self.balance_minor == self.original_amount_minor else "partial"

    def timing_state(self, today: date) -> str | None:
        if self.lifecycle_status != "open":
            return None
        if self.due_date is None:
            return "no_due_date"
        days = (self.due_date - today).days
        return "overdue" if days < 0 else "due_soon" if days <= 7 else "upcoming"

    def pay(self, amount: int, expected_version: int) -> "Commitment":
        if self.version != expected_version:
            raise DomainError(
                "VERSION_CONFLICT", "El saldo cambió. Revisa y confirma de nuevo.", 409
            )
        if self.lifecycle_status != "open":
            raise DomainError("COMMITMENT_NOT_OPEN", "Este pendiente ya no está abierto.")
        if amount <= 0:
            raise DomainError("INVALID_AMOUNT", "El abono debe ser mayor que cero.")
        if amount > self.balance_minor:
            raise DomainError("PAYMENT_EXCEEDS_BALANCE", "El abono supera el saldo pendiente.")
        balance = self.balance_minor - amount
        return replace(
            self,
            balance_minor=balance,
            version=self.version + 1,
            lifecycle_status="paid" if balance == 0 else "open",
        )
