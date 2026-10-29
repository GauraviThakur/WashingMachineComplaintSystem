
from io import BytesIO

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.services.report_service import generate_rejection_report


router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Complaint Reports"],
)


@router.get("/complaints/{complaint_number}/rejection.pdf")
def download_rejection_report(complaint_number: str):
    result = generate_rejection_report(complaint_number)

    error = result.get("error")

    if error == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if error == "complaint_not_rejected":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A rejection report is available only for rejected complaints.",
        )

    if error == "rejection_reason_missing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The rejection reason is missing. The report cannot be generated.",
        )

    if error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate the rejection report.",
        )

    filename = f"rejection_report_{result['complaint_number']}.pdf"

    return StreamingResponse(
        BytesIO(result["pdf_bytes"]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
