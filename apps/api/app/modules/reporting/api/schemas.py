from pydantic import (
    BaseModel,
    field_serializer,
)


class DashboardOut(BaseModel):
    currency_code: str
    receivable_balance_minor: int
    payable_balance_minor: int
    overdue_balance_minor: int
    due_soon_balance_minor: int
    active_commitments: int

    @field_serializer(
        "receivable_balance_minor",
        "payable_balance_minor",
        "overdue_balance_minor",
        "due_soon_balance_minor",
    )
    def exact_money(self, value: int) -> str:
        return str(value)
