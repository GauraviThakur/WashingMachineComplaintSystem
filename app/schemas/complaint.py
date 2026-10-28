
from pydantic import BaseModel, ConfigDict, Field


class ComplaintCreate(BaseModel):
    """Validate data submitted when registering a complaint."""

    serial_number: str = Field(
        min_length=1,
        max_length=100,
        description="Serial number of the returned washing machine",
    )

    customer_name: str = Field(
        min_length=2,
        max_length=150,
    )

    customer_contact: str | None = Field(
        default=None,
        max_length=30,
    )

    dealer_email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )

    reported_issue: str = Field(
        min_length=3,
        max_length=5000,
        description="Original problem statement received from the dealer",
    )

    issue_type_id: int | None = Field(
        default=None,
        ge=1,
        description="Optional issue classification",
    )

    registered_by: str = Field(
        default="system",
        min_length=1,
        max_length=150,
        description="Person registering the complaint",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
