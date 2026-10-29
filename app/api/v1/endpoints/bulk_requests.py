
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from app.services.bulk_request_service import (
    get_bulk_request_details,
    process_bulk_upload,
)


router = APIRouter(
    prefix="/api/v1/bulk-requests",
    tags=["Bulk Requests"],
)


@router.post("/upload")
async def upload_bulk_complaints(
    file: Annotated[UploadFile, File()],
    uploaded_by: Annotated[str, Form(min_length=1, max_length=150)] = "system",
):
    filename = file.filename or ""

    if not filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(
            status_code=422,
            detail="Unsupported file format. Upload a .csv or .xlsx file.",
        )

    content = await file.read()

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB.",
        )

    try:
        return process_bulk_upload(
            filename=filename,
            content=content,
            uploaded_by=uploaded_by.strip(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail="The uploaded file contains invalid data.",
        ) from exc


@router.get("/{bulk_request_id}")
def get_bulk_request(bulk_request_id: int):
    result = get_bulk_request_details(bulk_request_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Bulk request not found.",
        )

    return result
