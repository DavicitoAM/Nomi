from fastapi import APIRouter

from app.api.dependencies import Auth
from app.modules.reporting.api.schemas import DashboardOut
from app.modules.reporting.application.use_cases import get_dashboard
from app.shared.uow import SqlUnitOfWork

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardOut)
def dashboard(context: Auth):
    return get_dashboard(SqlUnitOfWork(), context)
