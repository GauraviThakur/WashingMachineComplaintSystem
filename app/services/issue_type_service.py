
from app.repositories.issue_type_repository import get_issue_types
from app.schemas.issue_type import IssueTypeResponse


def list_issue_types(
    category_id: int | None = None,
) -> list[IssueTypeResponse]:
    """Return active issue types, optionally filtered by category."""

    issue_types = get_issue_types(category_id)

    return [
        IssueTypeResponse.model_validate(issue_type)
        for issue_type in issue_types
    ]
