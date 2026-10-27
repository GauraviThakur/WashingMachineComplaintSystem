
from fastapi import APIRouter, HTTPException, status

from app.schemas.machine import MachineResponse
from app.services.machine_service import find_machine_by_serial_number


router = APIRouter(
    prefix="/machines",
    tags=["Machines"],
)


@router.get("/{serial_number}")
def get_machine(serial_number: str) -> dict:
    """Find and verify a machine using its serial number."""

    machine = find_machine_by_serial_number(serial_number)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Machine not found. Verify the serial number.",
                "status": "not_found",
            },
        )

    validated_machine = MachineResponse.model_validate(machine)

    return {
        "message": "Machine found successfully",
        "machine": validated_machine.model_dump(mode="json"),
    }
