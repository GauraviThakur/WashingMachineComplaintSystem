
from io import BytesIO
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.services.report_service import (
    generate_rejection_report,
    generate_individual_complaint_report,
)
from app.services.complaint_summary_report_service import (
    get_complaint_summary,
    generate_complaint_summary_pdf,
    generate_complaint_summary_excel,
)


router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Complaint Reports"],
)


# --------------------------------------------------
# INDIVIDUAL COMPLAINT REPORT - PDF DOWNLOAD
# --------------------------------------------------

@router.get("/complaints/{complaint_number}/pdf")
def download_individual_complaint_report(
    complaint_number: str,
):
    result = generate_individual_complaint_report(
        complaint_number
    )

    error = result.get("error")

    if error == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate the individual complaint report.",
        )

    filename = (
        f"complaint_report_{result['complaint_number']}.pdf"
    )

    return StreamingResponse(
        BytesIO(result["pdf_bytes"]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )


# --------------------------------------------------
# EXISTING REJECTION REPORT
# --------------------------------------------------

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


# --------------------------------------------------
# COMPLAINT SUMMARY REPORT - JSON DATA
# --------------------------------------------------

@router.get("/complaint-summary")
def complaint_summary(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
):
    try:
        return get_complaint_summary(
            from_date=from_date,
            to_date=to_date,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


# --------------------------------------------------
# COMPLAINT SUMMARY REPORT - PDF DOWNLOAD
# --------------------------------------------------

@router.get("/complaint-summary/pdf")
def download_complaint_summary_pdf(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
):
    try:
        result = generate_complaint_summary_pdf(
            from_date=from_date,
            to_date=to_date,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    filename = "complaint_summary_report.pdf"

    return StreamingResponse(
        result,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


# --------------------------------------------------
# COMPLAINT SUMMARY REPORT - EXCEL DOWNLOAD
# --------------------------------------------------

@router.get("/complaint-summary/excel")
def download_complaint_summary_excel(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
):
    try:
        result = generate_complaint_summary_excel(
            from_date=from_date,
            to_date=to_date,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    filename = "complaint_summary_report.xlsx"

    return StreamingResponse(
        result,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
