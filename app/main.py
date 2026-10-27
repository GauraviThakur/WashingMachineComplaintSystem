
from fastapi import FastAPI

from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.issue_types import router as issue_types_router
from app.api.v1.endpoints.machines import router as machines_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "An API-first complaint management system for returned "
        "washing machines, from complaint intake through final closure."
    ),
)


@app.get("/", tags=["General"])
def home() -> dict[str, str]:
    """Return the application welcome message."""

    return {
        "message": "Welcome to the Washing Machine Complaint Management System"
    }


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Confirm that the API process is responding."""

    return {
        "message": "Application is running",
        "status": "healthy",
    }


app.include_router(machines_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(issue_types_router, prefix="/api/v1")
