import re
from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum
from uuid import UUID

from app.shared.errors import DomainError

MAX_MONEY = 9_000_000_000_000  # minor units; safely representable by the web client


class Direction(StrEnum):
    RECEIVABLE = "receivable"
    PAYABLE = "payable"


class Lifecycle(StrEnum):
    OPEN = "open"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Commitment:
    id: UUID
    workspace_id: UUID
    contact_id: UUID
    direction: Direction
    original_amount_minor: int
    balance_minor: int
    currency_code: str
    concept: str | None
    due_date: date | None
    lifecycle_status: Lifecycle = Lifecycle.OPEN
    version: int = 1
    notes: str | None = None

    def __post_init__(self):
        if (
            type(self.original_amount_minor) is not int
            or not 0 < self.original_amount_minor <= MAX_MONEY
        ):
            raise DomainError("INVALID_AMOUNT", "El monto está fuera del rango permitido.")
        if (
            type(self.balance_minor) is not int
            or not 0 <= self.balance_minor <= self.original_amount_minor
        ):
            raise DomainError("INVALID_BALANCE", "El saldo está fuera del rango permitido.")
        if type(self.version) is not int or not 1 <= self.version <= 2147483647:
            raise DomainError("INVALID_VERSION", "La versión no es válida.")
        if self.direction not in ("receivable", "payable"):
            raise DomainError("INVALID_DIRECTION", "Dirección inválida.")
        object.__setattr__(self, "direction", Direction(self.direction))
        if not re.fullmatch(r"[A-Z]{3}", self.currency_code):
            raise DomainError("INVALID_CURRENCY", "La moneda no es válida.")
        if (
            self.lifecycle_status not in ("open", "paid", "cancelled")
            or (self.lifecycle_status == "open" and self.balance_minor == 0)
            or (self.lifecycle_status == "paid" and self.balance_minor != 0)
        ):
            raise DomainError("INVALID_LIFECYCLE", "El estado no corresponde al saldo.")
        object.__setattr__(self, "lifecycle_status", Lifecycle(self.lifecycle_status))

    def revise(self, expected_version: int, *, cancel=False, **changes) -> "Commitment":
        if type(expected_version) is not int or not 1 <= expected_version < 2147483647:
            raise DomainError("INVALID_VERSION", "La versión no es válida.")
        if self.version != expected_version:
            raise DomainError("VERSION_CONFLICT", "El pendiente cambió. Actualiza y revisa.", 409)
        if set(changes) - {"concept", "notes", "due_date"}:
            raise DomainError("IMMUTABLE_FIELD", "No puedes cambiar datos financieros.")
        if cancel and self.lifecycle_status != Lifecycle.OPEN:
            raise DomainError("COMMITMENT_NOT_OPEN", "Este pendiente ya no está abierto.", 409)
        return replace(
            self,
            **changes,
            version=self.version + 1,
            lifecycle_status=Lifecycle.CANCELLED if cancel else self.lifecycle_status,
        )

    def reverse_payment(self, amount: int, expected_version: int) -> "Commitment":
        if type(expected_version) is not int or not 1 <= expected_version < 2147483647:
            raise DomainError("INVALID_VERSION", "La versión no es válida.")
        if self.version != expected_version:
            raise DomainError(
                "VERSION_CONFLICT", "El saldo cambió. Revisa y confirma de nuevo.", 409
            )
        if self.lifecycle_status == Lifecycle.CANCELLED:
            raise DomainError(
                "COMMITMENT_CANCELLED", "No puedes revertir pagos de un pendiente cancelado.", 409
            )
        if type(amount) is not int or amount <= 0:
            raise DomainError("INVALID_AMOUNT", "El importe debe ser positivo.")
        if self.balance_minor + amount > self.original_amount_minor:
            raise DomainError("INVALID_REVERSAL", "La reversión excedería el monto original.", 409)
        return replace(
            self,
            balance_minor=self.balance_minor + amount,
            lifecycle_status=Lifecycle.OPEN,
            version=self.version + 1,
        )

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
        if type(expected_version) is not int or not 1 <= expected_version < 2147483647:
            raise DomainError("INVALID_VERSION", "La versión no es válida.")
        if self.version != expected_version:
            raise DomainError(
                "VERSION_CONFLICT", "El saldo cambió. Revisa y confirma de nuevo.", 409
            )
        if self.lifecycle_status != "open":
            raise DomainError("COMMITMENT_NOT_OPEN", "Este pendiente ya no está abierto.")
        if type(amount) is not int or amount <= 0:
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
