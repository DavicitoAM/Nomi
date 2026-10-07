from fastapi import APIRouter

from app.api.schemas import Problem
from app.modules.commitments.api.routes import router as commitments_router
from app.modules.contacts.api.routes import router as contacts_router
from app.modules.identity.api.routes import router as identity_router
from app.modules.reporting.api.export_routes import router as export_router
from app.modules.reporting.api.routes import router as reporting_router
from app.modules.transactions.api.routes import router as transactions_router

router = APIRouter(
    prefix="/api/v1",
    responses={
        status: {
            "model": Problem,
            "description": "Problem Details",
            "content": {"application/problem+json": {}},
        }
        for status in (400, 401, 403, 404, 408, 409, 413, 415, 422, 429, 503)
    },
)

router.include_router(identity_router)
router.include_router(contacts_router)
router.include_router(commitments_router)
router.include_router(transactions_router)
router.include_router(reporting_router)
router.include_router(export_router)
