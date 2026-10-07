from fastapi import APIRouter, Response

from app.api.dependencies import Auth
from app.modules.reporting.application.export import export_workspace
from app.shared.uow import SqlUnitOfWork

router = APIRouter()


@router.post(
    "/exports/workspace",
    response_class=Response,
    responses={
        200: {
            "description": "Workspace JSON, no credentials; at most 10,000 rows / 10 MB",
            "content": {"application/json": {"schema": {"type": "object"}}},
        }
    },
)
def export(context: Auth):
    return Response(
        export_workspace(SqlUnitOfWork(), context),
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="nomi-workspace.json"',
            "Cache-Control": "no-store",
        },
    )
