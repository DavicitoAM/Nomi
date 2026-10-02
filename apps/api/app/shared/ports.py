from typing import Any, Protocol


class UnitOfWork(Protocol):
    """Application boundary. Concrete repositories and transaction belong to infrastructure."""

    identity: Any
    workspaces: Any
    contacts: Any
    commitments: Any
    transactions: Any
    audit: Any
    effects: Any

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args) -> None: ...
    def commit(self) -> None: ...
