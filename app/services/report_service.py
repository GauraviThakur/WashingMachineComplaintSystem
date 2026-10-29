
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)

from app.database.connection import get_db_connection


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return "Not recorded"
    return str(value)


def _paragraph(value: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(
        escape(_format_value(value)).replace("\n", "<br/>"),
        style,
    )


def _add_section(
    story: list,
    title: str,
    rows: list[tuple[str, Any]],
    styles: dict,
) -> None:
    story.append(Paragraph(escape(title), styles["section"]))

    if not rows:
        story.append(
            Paragraph("No records available.", styles["body"])
        )
        story.append(Spacer(1, 3 * mm))
        return

    table_data = [
        [
            _paragraph(label, styles["label"]),
            _paragraph(value, styles["body"]),
        ]
        for label, value in rows
    ]

    table = Table(
        table_data,
        colWidths=[48 * mm, 122 * mm],
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#F1F5F9"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#CBD5E1"),
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 4 * mm))


def _fetch_report_data(
    complaint_number: str,
) -> dict[str, Any] | None:
    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT
                c.complaint_id,
                c.complaint_number,
                c.customer_name,
                c.customer_contact,
                c.dealer_email,
                c.reported_issue,
                c.priority,
                c.complaint_status,
                c.registered_at,
                m.serial_number,
                m.model_number,
                m.batch_number,
                m.manufacturing_date,

                COALESCE(
                    complaint_type.issue_type_name,
                    inspection_type.issue_type_name
                ) AS issue_type_name,

                COALESCE(
                    complaint_category.category_name,
                    inspection_category.category_name
                ) AS category_name,

                d.decision_type,
                d.decision_reason,
                d.rejection_reason,
                d.decided_by,
                d.decided_at,
                disp.disposition_type,
                disp.disposition_reason,
                disp.recorded_by AS disposition_recorded_by,
                disp.recorded_at AS disposition_recorded_at

            FROM complaints AS c

            INNER JOIN machines AS m
                ON m.machine_id = c.machine_id

            LEFT JOIN issue_types AS complaint_type
                ON complaint_type.issue_type_id = c.issue_type_id

            LEFT JOIN complaint_categories AS complaint_category
                ON complaint_category.category_id =
                   complaint_type.category_id

            LEFT JOIN LATERAL (
                SELECT
                    i.issue_type_id
                FROM inspections AS i
                WHERE i.complaint_id = c.complaint_id
                  AND i.issue_type_id IS NOT NULL
                ORDER BY
                    i.inspection_number DESC
                LIMIT 1
            ) AS latest_inspection
                ON TRUE

            LEFT JOIN issue_types AS inspection_type
                ON inspection_type.issue_type_id =
                   latest_inspection.issue_type_id

            LEFT JOIN complaint_categories AS inspection_category
                ON inspection_category.category_id =
                   inspection_type.category_id

            LEFT JOIN complaint_decisions AS d
                ON d.complaint_id = c.complaint_id

            LEFT JOIN complaint_dispositions AS disp
                ON disp.complaint_id = c.complaint_id

            WHERE c.complaint_number = %s
            """,
            (complaint_number,),
        ).fetchone()

        if complaint is None:
            return None

        if complaint["decision_type"] != "REJECTED":
            return {"error": "complaint_not_rejected"}

        complaint_id = complaint["complaint_id"]

        inspections = connection.execute(
            """
            SELECT
                inspection_number,
                inspected_by,
                inspection_findings,
                inspection_outcome,
                recommended_action,
                inspection_notes,
                inspected_at
            FROM inspections
            WHERE complaint_id = %s
            ORDER BY inspection_number
            """,
            (complaint_id,),
        ).fetchall()

        tests = connection.execute(
            """
            SELECT
                test_number,
                tested_by,
                test_type,
                test_result,
                test_observations,
                test_notes,
                tested_at
            FROM complaint_tests
            WHERE complaint_id = %s
            ORDER BY test_number
            """,
            (complaint_id,),
        ).fetchall()

        return {
            "complaint": dict(complaint),
            "inspections": [dict(row) for row in inspections],
            "tests": [dict(row) for row in tests],
        }


def generate_rejection_report(
    complaint_number: str,
) -> dict[str, Any]:
    data = _fetch_report_data(
        complaint_number.strip().upper()
    )

    if data is None:
        return {"error": "complaint_not_found"}

    if data.get("error"):
        return data

    complaint = data["complaint"]

    rejection_reason = complaint["rejection_reason"]

    if (
        rejection_reason is None
        or not str(rejection_reason).strip()
    ):
        return {"error": "rejection_reason_missing"}

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=(
            f"Rejection Decision Report - "
            f"{complaint['complaint_number']}"
        ),
        author="Washing Machine Complaint Management System",
    )

    base_styles = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "RejectionReportTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=21,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17365D"),
            spaceAfter=4 * mm,
        ),
        "subtitle": ParagraphStyle(
            "RejectionReportSubtitle",
            parent=base_styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=3 * mm,
        ),
        "section": ParagraphStyle(
            "RejectionReportSection",
            parent=base_styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#17365D"),
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        ),
        "label": ParagraphStyle(
            "RejectionReportLabel",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
        ),
        "body": ParagraphStyle(
            "RejectionReportBody",
            parent=base_styles["Normal"],
            fontSize=8,
            leading=11,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "RejectionReportSmall",
            parent=base_styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
        ),
    }

    story = [
        Paragraph(
            "WASHING MACHINE REJECTION DECISION REPORT",
            styles["title"],
        ),
        Paragraph(
            "Complaint: "
            f"{escape(_format_value(complaint['complaint_number']))}",
            styles["subtitle"],
        ),
        Paragraph(
            "Record of the rejection decision and its justification",
            styles["subtitle"],
        ),
        Spacer(1, 3 * mm),
    ]

    _add_section(
        story,
        "1. Complaint and Machine Identification",
        [
            ("Complaint number", complaint["complaint_number"]),
            ("Machine serial number", complaint["serial_number"]),
            ("Model number", complaint["model_number"]),
            ("Batch number", complaint["batch_number"]),
            ("Manufacturing date", complaint["manufacturing_date"]),
            ("Customer", complaint["customer_name"]),
            ("Customer contact", complaint["customer_contact"]),
            ("Dealer email", complaint["dealer_email"]),
            ("Issue category", complaint["category_name"]),
            ("Issue type", complaint["issue_type_name"]),
            ("Reported issue", complaint["reported_issue"]),
            ("Priority", complaint["priority"]),
            ("Complaint registered at", complaint["registered_at"]),
        ],
        styles,
    )

    _add_section(
        story,
        "2. Rejection Decision and Justification",
        [
            ("Decision", complaint["decision_type"]),
            ("Decision reason", complaint["decision_reason"]),
            ("Mandatory rejection reason", rejection_reason),
            ("Decision recorded by", complaint["decided_by"]),
            ("Decision date and time", complaint["decided_at"]),
        ],
        styles,
    )

    story.append(
        Paragraph(
            "3. Relevant Inspection Findings",
            styles["section"],
        )
    )

    if not data["inspections"]:
        story.append(
            Paragraph(
                "No inspection records were found for this complaint.",
                styles["body"],
            )
        )
    else:
        for item in data["inspections"]:
            inspection_content = [
                Paragraph(
                    "Inspection #"
                    f"{escape(_format_value(item['inspection_number']))}",
                    styles["section"],
                ),
                Paragraph(
                    "<b>Inspected by:</b> "
                    f"{escape(_format_value(item['inspected_by']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Findings:</b> "
                    f"{escape(_format_value(item['inspection_findings']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Outcome:</b> "
                    f"{escape(_format_value(item['inspection_outcome']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Recommended action:</b> "
                    f"{escape(_format_value(item['recommended_action']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Inspection notes:</b> "
                    f"{escape(_format_value(item['inspection_notes']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Inspected at:</b> "
                    f"{escape(_format_value(item['inspected_at']))}",
                    styles["body"],
                ),
                Spacer(1, 3 * mm),
            ]

            story.append(KeepTogether(inspection_content))

    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "4. Relevant Testing Results",
            styles["section"],
        )
    )

    if not data["tests"]:
        story.append(
            Paragraph(
                "No testing records were found for this complaint.",
                styles["body"],
            )
        )
    else:
        for item in data["tests"]:
            test_content = [
                Paragraph(
                    "Test #"
                    f"{escape(_format_value(item['test_number']))}",
                    styles["section"],
                ),
                Paragraph(
                    "<b>Test type:</b> "
                    f"{escape(_format_value(item['test_type']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Result:</b> "
                    f"{escape(_format_value(item['test_result']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Observations:</b> "
                    f"{escape(_format_value(item['test_observations']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Test notes:</b> "
                    f"{escape(_format_value(item['test_notes']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Tested by:</b> "
                    f"{escape(_format_value(item['tested_by']))}",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Tested at:</b> "
                    f"{escape(_format_value(item['tested_at']))}",
                    styles["body"],
                ),
                Spacer(1, 3 * mm),
            ]

            story.append(KeepTogether(test_content))

    if complaint["disposition_type"] is not None:
        _add_section(
            story,
            "5. Recorded Final Disposition",
            [
                ("Disposition", complaint["disposition_type"]),
                (
                    "Disposition reason",
                    complaint["disposition_reason"],
                ),
                (
                    "Recorded by",
                    complaint["disposition_recorded_by"],
                ),
                (
                    "Recorded at",
                    complaint["disposition_recorded_at"],
                ),
            ],
            styles,
        )

    story.append(Spacer(1, 5 * mm))
    story.append(
        Paragraph(
            "This report documents the recorded rejection decision "
            "and its supporting complaint, inspection, and testing "
            "information. A missing inspection or testing record "
            "means no corresponding record was found in the system; "
            "it does not establish that the activity was performed "
            "or that a particular result was obtained. This report "
            "does not, by itself, confirm that the complaint is "
            "closed or that final disposition has been completed.",
            styles["small"],
        )
    )

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return {
        "complaint_number": complaint["complaint_number"],
        "pdf_bytes": pdf_bytes,
    }
