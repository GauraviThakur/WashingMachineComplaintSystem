
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MachineResponse(BaseModel):
    """Machine information returned by the API."""

    machine_id: int
    serial_number: str
    model_number: str
    batch_number: str | None
    manufacturing_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
