
from fastapi import APIRouter

from app.schemas.category import CategoryResponse
from app.services.category_service import list_categories


router = APIRouter(
    prefix="/complaint-categories",
    tags=["Complaint Categories"],
)


@router.get("/")
def get_complaint_categories() -> dict:
    """Return all active complaint categories."""

    categories = list_categories()

    return {
        "message": "Complaint categories retrieved successfully",
        "total": len(categories),
        "categories": [
            category.model_dump(mode="json")
            for category in categories
        ],
    }
