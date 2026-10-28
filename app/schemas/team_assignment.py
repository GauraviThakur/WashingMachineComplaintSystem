
from pydantic import BaseModel, ConfigDict, Field


class TeamAssignmentCreate(BaseModel):
    complaint_number: str = Field(min_length=1, max_length=50)
    team_id: int = Field(ge=1)
    assigned_by: str = Field(min_length=1, max_length=150)
    assignment_reason: str = Field(min_length=3, max_length=2000)
    assigned_to: str | None = Field(default=None, max_length=150)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )


class AutomaticTeamAssignmentCreate(BaseModel):
    complaint_number: str = Field(min_length=1, max_length=50)
    assigned_by: str = Field(min_length=1, max_length=150)
    assigned_to: str | None = Field(default=None, max_length=150)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
