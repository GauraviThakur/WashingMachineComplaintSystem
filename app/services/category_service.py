
from app.repositories.category_repository import get_all_categories
from app.schemas.category import CategoryResponse


def list_categories() -> list[CategoryResponse]:
    """Return active complaint categories."""

    categories = get_all_categories()

    return [
        CategoryResponse.model_validate(category)
        for category in categories
    ]
