from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints.machines import router as machines_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.issue_types import router as issue_types_router
from app.api.v1.endpoints.complaints import router as complaints_router
from app.api.v1.endpoints.inspections import router as inspections_router
from app.api.v1.endpoints.team_assignments import router as team_assignments_router
from app.api.v1.endpoints.team_assessments import router as team_assessments_router
from app.api.v1.endpoints.rework import router as rework_router
from app.api.v1.endpoints.testing import router as testing_router
from app.api.v1.endpoints.decision_disposition import router as decision_disposition_router
from app.api.v1.endpoints.bulk_requests import router as bulk_requests_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.dashboard import router as dashboard_router


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"


app = FastAPI(
    title="Washing Machine Complaint Management System",
    description="Backend APIs for washing machine complaint management.",
    version="1.0.0",
)


# --------------------------------------------------
# Static files
# --------------------------------------------------

app.mount(
    "/assets",
    StaticFiles(directory=str(ASSETS_DIR)),
    name="assets",
)


# --------------------------------------------------
# Frontend page routes
# --------------------------------------------------

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/complaints", include_in_schema=False)
def complaints_page():
    return FileResponse(FRONTEND_DIR / "complaints.html")


@app.get("/register-complaint", include_in_schema=False)
def register_complaint_page():
    return FileResponse(FRONTEND_DIR / "register-complaint.html")


@app.get("/bulk-upload", include_in_schema=False)
def bulk_upload_page():
    return FileResponse(FRONTEND_DIR / "bulk-upload.html")


@app.get("/bulk-tracking", include_in_schema=False)
def bulk_tracking_page():
    return FileResponse(FRONTEND_DIR / "bulk-tracking.html")


@app.get("/inspection", include_in_schema=False)
def inspection_page():
    return FileResponse(FRONTEND_DIR / "inspection.html")


@app.get("/rework", include_in_schema=False)
def rework_page():
    return FileResponse(FRONTEND_DIR / "rework.html")


@app.get("/team-assessment", include_in_schema=False)
def team_assessment_page():
    return FileResponse(FRONTEND_DIR / "team-assessment.html")


@app.get("/testing", include_in_schema=False)
def testing_page():
    return FileResponse(FRONTEND_DIR / "testing.html")


@app.get("/quality-decision", include_in_schema=False)
def quality_decision_page():
    return FileResponse(FRONTEND_DIR / "quality-decision.html")


@app.get("/reports", include_in_schema=False)
def reports_page():
    return FileResponse(FRONTEND_DIR / "reports.html")


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/api/v1/health")
def health_check():
    return {
        "message": "Application is running",
        "status": "healthy",
    }


# --------------------------------------------------
# API routers
# --------------------------------------------------

app.include_router(machines_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(issue_types_router, prefix="/api/v1")
app.include_router(complaints_router, prefix="/api/v1")
app.include_router(inspections_router, prefix="/api/v1")

app.include_router(team_assignments_router)
app.include_router(team_assessments_router)

app.include_router(rework_router)
app.include_router(testing_router)
app.include_router(decision_disposition_router)
app.include_router(bulk_requests_router)
app.include_router(reports_router)
app.include_router(dashboard_router)
