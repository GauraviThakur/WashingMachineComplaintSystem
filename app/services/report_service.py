
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

    table_data = [
        [
            _paragraph(label, styles["label"]),
            _paragraph(value, styles["body"]),
        ]
        for label, value in rows
    ]

    if not table_data:
        story.append(Paragraph("No records available.", styles["body"]))
        return

    table = Table(
        table_data,
        colWidths=[48 * mm, 122 * mm],
        repeatRows=0,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 5 * mm))


def _fetch_report_data(complaint_number: str) -> dict[str, Any] | None:
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
                c.is_repeat_complaint,
                c.registered_at,
                c.closed_at,
                m.serial_number,
                m.model_number,
                m.batch_number,
                m.manufacturing_date,
                it.issue_type_name,
                cc.category_name,
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
            LEFT JOIN issue_types AS it
                ON it.issue_type_id = c.issue_type_id
            LEFT JOIN complaint_categories AS cc
                ON cc.category_id = it.category_id
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
                issue_type_id,
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

        rework_attempts = connection.execute(
            """
            SELECT
                attempt_number,
                performed_by,
                rework_action,
                parts_replaced,
                rework_result,
                requires_testing,
                rework_notes,
                started_at,
                completed_at
            FROM rework_attempts
            WHERE complaint_id = %s
            ORDER BY attempt_number
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

        history = connection.execute(
            """
            SELECT
                previous_status,
                new_status,
                changed_by,
                reason,
                changed_at
            FROM complaint_history
            WHERE complaint_id = %s
            ORDER BY changed_at, history_id
            """,
            (complaint_id,),
        ).fetchall()

        return {
            "complaint": dict(complaint),
            "inspections": [dict(row) for row in inspections],
            "rework_attempts": [dict(row) for row in rework_attempts],
            "tests": [dict(row) for row in tests],
            "history": [dict(row) for row in history],
        }


def generate_rejection_report(
    complaint_number: str,
) -> dict[str, Any]:
    data = _fetch_report_data(complaint_number.strip().upper())

    if data is None:
        return {"error": "complaint_not_found"}

    if data.get("error"):
        return data

    complaint = data["complaint"]

    if not complaint["rejection_reason"] or not str(
        complaint["rejection_reason"]
    ).strip():
        return {"error": "rejection_reason_missing"}

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Rejection Report - {complaint['complaint_number']}",
        author="Washing Machine Complaint Management System",
    )

    base_styles = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17365D"),
            spaceAfter=5 * mm,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base_styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=6 * mm,
        ),
        "section": ParagraphStyle(
            "SectionHeading",
            parent=base_styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#17365D"),
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        ),
        "label": ParagraphStyle(
            "FieldLabel",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
        ),
        "body": ParagraphStyle(
            "FieldValue",
            parent=base_styles["Normal"],
            fontSize=8,
            leading=11,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "SmallText",
            parent=base_styles["Normal"],
            fontSize=8,
            leading=11,
        ),
    }

    story = [
        Paragraph("WASHING MACHINE REJECTION REPORT", styles["title"]),
        Paragraph(
            f"Complaint: {escape(complaint['complaint_number'])}",
            styles["subtitle"],
        ),
        Paragraph(
            "Quality decision and rejection documentation",
            styles["subtitle"],
        ),
    ]

    _add_section(
        story,
        "1. Complaint and Machine Details",
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
            ("Registered at", complaint["registered_at"]),
            ("Repeat complaint", complaint["is_repeat_complaint"]),
            ("Current status", complaint["complaint_status"]),
        ],
        styles,
    )

    story.append(Paragraph("2. Inspection History", styles["section"]))

    if not data["inspections"]:
        story.append(
            Paragraph("No inspection records found.", styles["body"])
        )
    else:
        for item in data["inspections"]:
            story.append(
                KeepTogether(
                    [
                        Paragraph(
                            f"Inspection #{item['inspection_number']}",
                            styles["section"],
                        ),
                        Paragraph(
                            f"<b>Inspected by:</b> "
                            f"{escape(_format_value(item['inspected_by']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Findings:</b> "
                            f"{escape(_format_value(item['inspection_findings']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Outcome:</b> "
                            f"{escape(_format_value(item['inspection_outcome']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Recommended action:</b> "
                            f"{escape(_format_value(item['recommended_action']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Notes:</b> "
                            f"{escape(_format_value(item['inspection_notes']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Inspected at:</b> "
                            f"{escape(_format_value(item['inspected_at']))}",
                            styles["body"],
                        ),
                        Spacer(1, 3 * mm),
                    ]
                )
            )

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("3. Rework History", styles["section"]))

    if not data["rework_attempts"]:
        story.append(
            Paragraph("No rework records found.", styles["body"])
        )
    else:
        for item in data["rework_attempts"]:
            story.append(
                KeepTogether(
                    [
                        Paragraph(
                            f"Rework Attempt #{item['attempt_number']}",
                            styles["section"],
                        ),
                        Paragraph(
                            f"<b>Performed by:</b> "
                            f"{escape(_format_value(item['performed_by']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Action:</b> "
                            f"{escape(_format_value(item['rework_action']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Parts replaced:</b> "
                            f"{escape(_format_value(item['parts_replaced']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Result:</b> "
                            f"{escape(_format_value(item['rework_result']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Testing required:</b> "
                            f"{escape(_format_value(item['requires_testing']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Notes:</b> "
                            f"{escape(_format_value(item['rework_notes']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Started:</b> "
                            f"{escape(_format_value(item['started_at']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Completed:</b> "
                            f"{escape(_format_value(item['completed_at']))}",
                            styles["body"],
                        ),
                        Spacer(1, 3 * mm),
                    ]
                )
            )

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("4. Testing History", styles["section"]))

    if not data["tests"]:
        story.append(
            Paragraph("No testing records found.", styles["body"])
        )
    else:
        for item in data["tests"]:
            story.append(
                KeepTogether(
                    [
                        Paragraph(
                            f"Test Attempt #{item['test_number']}",
                            styles["section"],
                        ),
                        Paragraph(
                            f"<b>Test type:</b> "
                            f"{escape(_format_value(item['test_type']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Result:</b> "
                            f"{escape(_format_value(item['test_result']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Observations:</b> "
                            f"{escape(_format_value(item['test_observations']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Notes:</b> "
                            f"{escape(_format_value(item['test_notes']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Tested by:</b> "
                            f"{escape(_format_value(item['tested_by']))}",
                            styles["body"],
                        ),
                        Paragraph(
                            f"<b>Tested at:</b> "
                            f"{escape(_format_value(item['tested_at']))}",
                            styles["body"],
                        ),
                        Spacer(1, 3 * mm),
                    ]
                )
            )

    _add_section(
        story,
        "5. Final Rejection Decision",
        [
            ("Decision", complaint["decision_type"]),
            ("Decision reason", complaint["decision_reason"]),
            ("Rejection reason", complaint["rejection_reason"]),
            ("Decided by", complaint["decided_by"]),
            ("Decision timestamp", complaint["decided_at"]),
        ],
        styles,
    )

    _add_section(
        story,
        "6. Final Disposition",
        [
            ("Disposition", complaint["disposition_type"]),
            ("Disposition reason", complaint["disposition_reason"]),
            ("Recorded by", complaint["disposition_recorded_by"]),
            ("Disposition timestamp", complaint["disposition_recorded_at"]),
            ("Complaint closed at", complaint["closed_at"]),
        ],
        styles,
    )

    story.append(Paragraph("7. Complaint Audit History", styles["section"]))

    if not data["history"]:
        story.append(
            Paragraph("No complaint history records found.", styles["body"])
        )
    else:
        for item in data["history"]:
            transition = (
                f"{_format_value(item['previous_status'])} → "
                f"{_format_value(item['new_status'])}"
            )
            _add_section(
                story,
                transition,
                [
                    ("Changed by", item["changed_by"]),
                    ("Reason", item["reason"]),
                    ("Timestamp", item["changed_at"]),
                ],
                styles,
            )

    story.append(Spacer(1, 5 * mm))
    story.append(
        Paragraph(
            "This report was generated from records stored in the "
            "Washing Machine Complaint Management System. "
            "Verify the recorded information against the original "
            "inspection and quality records when required.",
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
