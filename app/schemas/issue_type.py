
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IssueTypeResponse(BaseModel):
    """Issue-type information returned by the API."""

    issue_type_id: int
    category_id: int
    category_name: str
    issue_type_name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
