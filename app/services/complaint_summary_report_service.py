from datetime import date, datetime, time
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from app.database.connection import get_db_connection


def _fetch_summary_data(
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict[str, Any]:
    """Fetch complaint summary and detailed complaint records."""

    conditions = []
    parameters = []

    if from_date:
        conditions.append("c.registered_at >= %s")
        parameters.append(from_date)

    if to_date:
        conditions.append("c.registered_at < %s")
        parameters.append(to_date + date.resolution)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    with get_db_connection() as connection:

        summary = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_complaints,

                COUNT(*) FILTER (
                    WHERE c.complaint_status <> 'CLOSED'
                ) AS open_complaints,

                COUNT(*) FILTER (
                    WHERE c.complaint_status = 'CLOSED'
                ) AS closed_complaints,

                COUNT(*) FILTER (
                    WHERE c.is_repeat_complaint = TRUE
                ) AS repeat_complaints,

                COUNT(*) FILTER (
                    WHERE d.decision_type = 'ACCEPTED'
                ) AS accepted_complaints,

                COUNT(*) FILTER (
                    WHERE d.decision_type = 'REJECTED'
                ) AS rejected_complaints

            FROM complaints AS c

            LEFT JOIN complaint_decisions AS d
                ON d.complaint_id = c.complaint_id

            {where_clause}
            """,
            parameters,
        ).fetchone()

        status_rows = connection.execute(
            f"""
            SELECT
                c.complaint_status,
                COUNT(*) AS complaint_count

            FROM complaints AS c

            {where_clause}

            GROUP BY c.complaint_status
            ORDER BY complaint_count DESC
            """,
            parameters,
        ).fetchall()

        category_rows = connection.execute(
            f"""
            SELECT
                COALESCE(
                    cc.category_name,
                    'Not Categorized'
                ) AS category_name,

                COUNT(*) AS complaint_count

            FROM complaints AS c

            LEFT JOIN issue_types AS it
                ON it.issue_type_id = c.issue_type_id

            LEFT JOIN complaint_categories AS cc
                ON cc.category_id = it.category_id

            {where_clause}

            GROUP BY cc.category_name
            ORDER BY complaint_count DESC
            """,
            parameters,
        ).fetchall()

        priority_rows = connection.execute(
            f"""
            SELECT
                c.priority,
                COUNT(*) AS complaint_count

            FROM complaints AS c

            {where_clause}

            GROUP BY c.priority
            ORDER BY complaint_count DESC
            """,
            parameters,
        ).fetchall()

        complaint_rows = connection.execute(
            f"""
            SELECT
                c.complaint_number,
                m.serial_number,
                m.model_number,
                c.customer_name,
                COALESCE(
                    cc.category_name,
                    'Not Categorized'
                ) AS category_name,
                COALESCE(
                    it.issue_type_name,
                    'Not Categorized'
                ) AS issue_type_name,
                c.priority,
                c.complaint_status,
                d.decision_type,
                disp.disposition_type,
                c.is_repeat_complaint,
                c.registered_at,
                c.closed_at

            FROM complaints AS c

            INNER JOIN machines AS m
                ON m.machine_id = c.machine_id

            LEFT JOIN issue_types AS it
                ON it.issue_type_id = c.issue_type_id

            LEFT JOIN complaint_categories AS cc
                ON cc.category_id = it.category_id

            LEFT JOIN complaint_decisions AS d
                ON d.complaint_id = c.complaint_id

            LEFT JOIN complaint_dispositions AS disp
                ON disp.complaint_id = c.complaint_id

            {where_clause}

            ORDER BY c.registered_at DESC
            """,
            parameters,
        ).fetchall()

    return {
        "summary": dict(summary),
        "statuses": [dict(row) for row in status_rows],
        "categories": [dict(row) for row in category_rows],
        "priorities": [dict(row) for row in priority_rows],
        "complaints": [dict(row) for row in complaint_rows],
        "from_date": from_date,
        "to_date": to_date,
        "generated_at": datetime.now().astimezone(),
    }


def get_complaint_summary(
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict[str, Any]:
    """Return complaint summary data for the frontend."""

    if from_date and to_date and from_date > to_date:
        raise ValueError("From date cannot be after To date.")

    return _fetch_summary_data(from_date, to_date)


def _excel_value(value: Any) -> Any:
    """Convert database values into Excel-compatible values."""

    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)

    if isinstance(value, time):
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)

    if isinstance(value, (date, datetime, time)):
        return value

    if isinstance(value, (list, tuple)):
        return "; ".join(str(item) for item in value)

    return value


def _format_worksheet(worksheet) -> None:
    """Apply formatting to Excel worksheets."""

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="173B63",
    )

    for cell in worksheet[1]:
        cell.font = Font(
            bold=True,
            color="FFFFFF",
        )
        cell.fill = header_fill
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    worksheet.freeze_panes = "A2"

    if worksheet.max_row > 1:
        worksheet.auto_filter.ref = worksheet.dimensions

    worksheet.row_dimensions[1].height = 30

    for column_cells in worksheet.columns:
        column_letter = get_column_letter(
            column_cells[0].column
        )

        maximum_length = 0

        for cell in column_cells:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

            if cell.value is not None:
                maximum_length = max(
                    maximum_length,
                    len(str(cell.value)),
                )

        worksheet.column_dimensions[column_letter].width = min(
            max(maximum_length + 3, 14),
            40,
        )


def generate_complaint_summary_excel(
    from_date: date | None = None,
    to_date: date | None = None,
) -> BytesIO:
    """Generate a multi-sheet Excel complaint summary report."""

    data = _fetch_summary_data(from_date, to_date)

    workbook = Workbook()

    # Sheet 1: Summary
    summary_sheet = workbook.active
    summary_sheet.title = "Summary"

    summary_sheet.append(["Complaint Summary Report"])
    summary_sheet.append(["Report Generated", data["generated_at"].replace(tzinfo=None)])
    summary_sheet.append([
        "From Date",
        from_date,
    ])
    summary_sheet.append([
        "To Date",
        to_date,
    ])
    summary_sheet.append([])
    summary_sheet.append(["Metric", "Count"])

    summary_fields = [
        ("Total Complaints", "total_complaints"),
        ("Open Complaints", "open_complaints"),
        ("Closed Complaints", "closed_complaints"),
        ("Repeat Complaints", "repeat_complaints"),
        ("Accepted Complaints", "accepted_complaints"),
        ("Rejected Complaints", "rejected_complaints"),
    ]

    for label, key in summary_fields:
        summary_sheet.append([
            label,
            data["summary"][key],
        ])

    # Sheet 2: Status
    status_sheet = workbook.create_sheet("Status Breakdown")
    status_sheet.append(["Complaint Status", "Count"])

    for row in data["statuses"]:
        status_sheet.append([
            row["complaint_status"],
            row["complaint_count"],
        ])

    # Sheet 3: Category
    category_sheet = workbook.create_sheet("Category Breakdown")
    category_sheet.append(["Category", "Count"])

    for row in data["categories"]:
        category_sheet.append([
            row["category_name"],
            row["complaint_count"],
        ])

    # Sheet 4: Priority
    priority_sheet = workbook.create_sheet("Priority Breakdown")
    priority_sheet.append(["Priority", "Count"])

    for row in data["priorities"]:
        priority_sheet.append([
            row["priority"],
            row["complaint_count"],
        ])

    # Sheet 5: Complaint Details
    details_sheet = workbook.create_sheet("Complaint Details")

    headers = [
        "Complaint Number",
        "Machine Serial Number",
        "Model Number",
        "Customer",
        "Category",
        "Issue Type",
        "Priority",
        "Status",
        "Decision",
        "Disposition",
        "Repeat Complaint",
        "Registered At",
        "Closed At",
    ]

    details_sheet.append(headers)

    for row in data["complaints"]:
        details_sheet.append([
            _excel_value(row["complaint_number"]),
            _excel_value(row["serial_number"]),
            _excel_value(row["model_number"]),
            _excel_value(row["customer_name"]),
            _excel_value(row["category_name"]),
            _excel_value(row["issue_type_name"]),
            _excel_value(row["priority"]),
            _excel_value(row["complaint_status"]),
            _excel_value(row["decision_type"]),
            _excel_value(row["disposition_type"]),
            _excel_value(row["is_repeat_complaint"]),
            _excel_value(row["registered_at"]),
            _excel_value(row["closed_at"]),
        ])

    for worksheet in workbook.worksheets:
        if worksheet.title == "Summary":
            continue

        _format_worksheet(worksheet)

    # Style the summary sheet separately.
    summary_sheet.merge_cells("A1:B1")
    summary_sheet["A1"].font = Font(
        bold=True,
        size=16,
        color="173B63",
    )
    summary_sheet["A1"].alignment = Alignment(
        horizontal="center",
    )

    for cell in summary_sheet[6]:
        cell.font = Font(
            bold=True,
            color="FFFFFF",
        )
        cell.fill = PatternFill(
            fill_type="solid",
            fgColor="173B63",
        )

    summary_sheet.column_dimensions["A"].width = 28
    summary_sheet.column_dimensions["B"].width = 28

    output = BytesIO()
    workbook.save(output)
    workbook.close()
    output.seek(0)

    return output


def generate_complaint_summary_pdf(
    from_date: date | None = None,
    to_date: date | None = None,
) -> BytesIO:
    """Generate a PDF complaint summary report."""

    data = _fetch_summary_data(from_date, to_date)

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Washing Machine Complaint Summary Report",
        author="Washing Machine Complaint Management System",
    )

    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SummaryTitle",
        parent=base_styles["Title"],
        fontSize=17,
        textColor=colors.HexColor("#173B63"),
        alignment=TA_CENTER,
        spaceAfter=5 * mm,
    )

    section_style = ParagraphStyle(
        "SummarySection",
        parent=base_styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#173B63"),
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )

    body_style = ParagraphStyle(
        "SummaryBody",
        parent=base_styles["Normal"],
        fontSize=8,
        leading=11,
    )

    story = [
        Paragraph(
            "WASHING MACHINE COMPLAINT SUMMARY REPORT",
            title_style,
        ),
        Paragraph(
            f"Generated: {data['generated_at'].strftime('%d-%m-%Y %H:%M:%S %Z')}",
            body_style,
        ),
        Paragraph(
            "Reporting period: "
            f"{from_date.isoformat() if from_date else 'All dates'} "
            "to "
            f"{to_date.isoformat() if to_date else 'All dates'}",
            body_style,
        ),
        Spacer(1, 5 * mm),
        Paragraph("1. Complaint Overview", section_style),
    ]

    summary = data["summary"]

    overview_rows = [
        ["Metric", "Count"],
        ["Total Complaints", summary["total_complaints"]],
        ["Open Complaints", summary["open_complaints"]],
        ["Closed Complaints", summary["closed_complaints"]],
        ["Repeat Complaints", summary["repeat_complaints"]],
        ["Accepted Decisions", summary["accepted_complaints"]],
        ["Rejected Decisions", summary["rejected_complaints"]],
    ]

    overview_table = Table(
        overview_rows,
        colWidths=[95 * mm, 45 * mm],
        repeatRows=1,
    )

    overview_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B63")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#F1F5F9"),
            ]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(overview_table)

    breakdowns = [
        (
            "2. Complaint Status Breakdown",
            "complaint_status",
            data["statuses"],
        ),
        (
            "3. Category Breakdown",
            "category_name",
            data["categories"],
        ),
        (
            "4. Priority Breakdown",
            "priority",
            data["priorities"],
        ),
    ]

    for title, label_key, rows in breakdowns:
        story.append(Paragraph(title, section_style))

        table_data = [["Name", "Complaint Count"]]

        for row in rows:
            table_data.append([
                str(row[label_key] or "Not recorded"),
                str(row["complaint_count"]),
            ])

        if len(table_data) == 1:
            table_data.append(["No records", "0"])

        table = Table(
            table_data,
            colWidths=[100 * mm, 40 * mm],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B63")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F1F5F9"),
                ]),
                ("PADDING", (0, 0), (-1, -1), 6),
            ])
        )

        story.append(table)

    story.append(PageBreak())
    story.append(
        Paragraph(
            "5. Complaint Details",
            section_style,
        )
    )

    detail_headers = [
        "Complaint No.",
        "Machine Serial",
        "Customer",
        "Category",
        "Priority",
        "Status",
        "Decision",
        "Registered",
    ]

    detail_data = [detail_headers]

    for row in data["complaints"]:
        detail_data.append([
            str(row["complaint_number"] or ""),
            str(row["serial_number"] or ""),
            str(row["customer_name"] or ""),
            str(row["category_name"] or ""),
            str(row["priority"] or ""),
            str(row["complaint_status"] or ""),
            str(row["decision_type"] or "Pending"),
            (
                row["registered_at"].strftime("%d-%m-%Y")
                if row["registered_at"]
                else ""
            ),
        ])

    if len(detail_data) == 1:
        detail_data.append(["No complaints found"] + [""] * 7)

    detail_table = Table(
        detail_data,
        colWidths=[
            36 * mm,
            30 * mm,
            35 * mm,
            28 * mm,
            18 * mm,
            30 * mm,
            23 * mm,
            22 * mm,
        ],
        repeatRows=1,
    )

    detail_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B63")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#F1F5F9"),
            ]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ])
    )

    story.append(detail_table)

    story.append(Spacer(1, 5 * mm))
    story.append(
        Paragraph(
            "Note: Open complaints are records whose current status "
            "is not CLOSED. Accepted and rejected counts represent "
            "recorded quality decisions and are independent of closure. "
            "The report is based on complaint registration date.",
            body_style,
        )
    )

    document.build(story)

    buffer.seek(0)
    return buffer