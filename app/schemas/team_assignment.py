
from pydantic import BaseModel, ConfigDict, Field


class TeamAssignmentCreate(BaseModel):
    """Validate a request to assign or reassign a complaint."""

    complaint_number: str = Field(
        min_length=1,
        max_length=50,
        description="Complaint number to assign",
    )
    team_id: int = Field(
        ge=1,
        description="ID of the responsible team",
    )
    assigned_by: str = Field(
        min_length=1,
        max_length=150,
        description="Person making the assignment",
    )
    assignment_reason: str = Field(
        min_length=3,
        max_length=2000,
        description="Reason for assigning or reassigning the complaint",
    )
    assigned_to: str | None = Field(
        default=None,
        max_length=150,
        description="Optional name of the person receiving the assignment",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
