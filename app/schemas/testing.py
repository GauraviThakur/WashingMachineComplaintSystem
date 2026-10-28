
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TestCreate(BaseModel):
    complaint_number: str = Field(min_length=1, max_length=50)
    tested_by: str = Field(min_length=2, max_length=150)
    test_type: str = Field(min_length=2, max_length=100)
    test_result: Literal["PASS", "FAIL"]
    test_observations: str = Field(min_length=3, max_length=5000)
    test_notes: str | None = Field(default=None, max_length=5000)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
