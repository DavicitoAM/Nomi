from typing import Any, Protocol

from app.modules.commitments.application.ports import Commitments
from app.modules.contacts.application.ports import Contacts
from app.modules.transactions.application.ports import Transactions


class UnitOfWork(Protocol):
    """Application boundary. Concrete repositories and transaction belong to infrastructure."""

    identity: Any
    workspaces: Any
    contacts: Contacts
    commitments: Commitments
    transactions: Transactions
    audit: Any
    effects: Any

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args) -> None: ...
    def commit(self) -> None: ...
    def consistent_read(self) -> None: ...
