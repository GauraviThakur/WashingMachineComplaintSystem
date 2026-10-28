
from app.repositories.testing_repository import (
    create_test_record,
    get_test_history,
)
from app.schemas.testing import TestCreate


def record_test(test_data: TestCreate) -> dict:
    complaint_number = test_data.complaint_number.strip().upper()

    result = create_test_record(
        complaint_number=complaint_number,
        tested_by=test_data.tested_by,
        test_type=test_data.test_type,
        test_result=test_data.test_result,
        test_observations=test_data.test_observations,
        test_notes=test_data.test_notes,
    )

    if result.get("error"):
        return result

    return result


def fetch_test_history(complaint_number: str) -> dict | None:
    normalized_complaint_number = complaint_number.strip().upper()

    return get_test_history(normalized_complaint_number)
