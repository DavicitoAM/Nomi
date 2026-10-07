from zoneinfo import ZoneInfo

from app.shared.context import now
from app.shared.ports import UnitOfWork


def get_dashboard(uow: UnitOfWork, context):
    with uow:
        today = now().astimezone(ZoneInfo(context.timezone)).date()
        return {
            "currency_code": context.currency,
            **uow.commitments.summary(context.workspace_id, today),
        }
