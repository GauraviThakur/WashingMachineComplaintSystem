
from fastapi import FastAPI

from app.api.v1.endpoints.machines import router as machines_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.issue_types import router as issue_types_router
from app.api.v1.endpoints.complaints import router as complaints_router
from app.api.v1.endpoints.inspections import router as inspections_router
from app.api.v1.endpoints.team_assignments import (
    router as team_assignments_router,
)
from app.api.v1.endpoints.rework import router as rework_router
from app.api.v1.endpoints.testing import router as testing_router
from app.api.v1.endpoints.decision_disposition import (
    router as decision_disposition_router,
)
from app.api.v1.endpoints.bulk_requests import router as bulk_requests_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.dashboard import router as dashboard_router


app = FastAPI(
    title="Washing Machine Complaint Management System",
    description="Backend APIs for washing machine complaint management.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to the Washing Machine Complaint Management System"
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "message": "Application is running",
        "status": "healthy",
    }


app.include_router(machines_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(issue_types_router, prefix="/api/v1")
app.include_router(complaints_router, prefix="/api/v1")
app.include_router(inspections_router, prefix="/api/v1")

# These routers already define their own /api/v1 prefixes.
app.include_router(team_assignments_router)
app.include_router(rework_router)
app.include_router(testing_router)
app.include_router(decision_disposition_router)
app.include_router(bulk_requests_router)
app.include_router(reports_router)
app.include_router(dashboard_router)
