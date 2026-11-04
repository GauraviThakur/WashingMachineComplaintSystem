
const API_BASE_URL = "/api/v1/reports";

document.addEventListener("DOMContentLoaded", () => {
    const previewButton = document.getElementById("previewButton");
    const pdfButton = document.getElementById("pdfButton");
    const excelButton = document.getElementById("excelButton");
    const rejectionButton = document.getElementById("rejectionButton");
    const individualReportButton = document.getElementById("individualReportButton");

    if (previewButton) {
        previewButton.addEventListener("click", previewSummary);
    }

    if (pdfButton) {
        pdfButton.addEventListener("click", downloadSummaryPDF);
    }

    if (excelButton) {
        excelButton.addEventListener("click", downloadSummaryExcel);
    }

    if (rejectionButton) {
        rejectionButton.addEventListener("click", downloadRejectionReport);
    }

    if (individualReportButton) {
        individualReportButton.addEventListener("click", downloadIndividualComplaintReport);
    }
});


/* =========================================
   1. COMMON HELPERS
========================================= */

function getDateFilters() {
    const fromDate = document.getElementById("fromDate").value;
    const toDate = document.getElementById("toDate").value;

    if (fromDate && toDate && fromDate > toDate) {
        showMessage("From Date cannot be later than To Date.", "danger");
        return null;
    }

    const params = new URLSearchParams();

    if (fromDate) {
        params.append("from_date", fromDate);
    }

    if (toDate) {
        params.append("to_date", toDate);
    }

    return params.toString();
}


function showMessage(message, type = "info") {
    const messageElement = document.getElementById("message");

    if (!messageElement) {
        return;
    }

    messageElement.className = `alert alert-${type}`;
    messageElement.textContent = message;
    messageElement.style.display = "block";
}


function hideMessage() {
    const messageElement = document.getElementById("message");

    if (messageElement) {
        messageElement.style.display = "none";
    }
}


function setButtonLoading(button, loading, originalText) {
    if (!button) {
        return;
    }

    button.disabled = loading;

    if (loading) {
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    } else {
        button.innerHTML = button.dataset.originalText || originalText;
    }
}


function formatDateTime(value) {
    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString("en-IN");
}


function formatLabel(value) {
    if (!value) {
        return "—";
    }

    return String(value)
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/\b\w/g, character => character.toUpperCase());
}


function escapeHTML(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================
   2. PREVIEW COMPLAINT SUMMARY
========================================= */

async function previewSummary() {
    hideMessage();

    const queryString = getDateFilters();

    if (queryString === null) {
        return;
    }

    const button = document.getElementById("previewButton");
    const previewContainer = document.getElementById("summaryPreview");

    setButtonLoading(button, true, "Preview Summary");

    previewContainer.innerHTML = `
        <div class="text-center text-secondary py-4">
            <div class="spinner-border spinner-border-sm me-2"></div>
            Loading complaint summary...
        </div>
    `;

    try {
        const url = queryString
            ? `${API_BASE_URL}/complaint-summary?${queryString}`
            : `${API_BASE_URL}/complaint-summary`;

        const response = await fetch(url);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));

            throw new Error(
                errorData.detail || "Unable to load complaint summary."
            );
        }

        const result = await response.json();

        renderSummary(result);

        showMessage("Complaint summary loaded successfully.", "success");

    } catch (error) {
        previewContainer.innerHTML = `
            <p class="text-danger small">
                ${escapeHTML(error.message)}
            </p>
        `;

        showMessage(error.message, "danger");

    } finally {
        setButtonLoading(button, false, "Preview Summary");
    }
}


/* =========================================
   3. RENDER SUMMARY
========================================= */

function renderSummary(result) {
    const previewContainer = document.getElementById("summaryPreview");

    const summary = result.summary || {};

    const statusRows = result.statuses || [];
    const categoryRows = result.categories || [];
    const priorityRows = result.priorities || [];

    previewContainer.innerHTML = `
        ${renderSummaryCards(summary)}

        <div class="row g-3 report-breakdown">

            <div class="col-lg-6">
                ${renderBreakdown(
                    "Status Breakdown",
                    statusRows,
                    "complaint_status"
                )}
            </div>

            <div class="col-lg-6">
                ${renderBreakdown(
                    "Category Breakdown",
                    categoryRows,
                    "category_name"
                )}
            </div>

            <div class="col-lg-6">
                ${renderBreakdown(
                    "Priority Breakdown",
                    priorityRows,
                    "priority"
                )}
            </div>

        </div>

        <p class="text-secondary small mt-4 mb-0">
            Report generated: ${escapeHTML(formatDateTime(result.generated_at))}
        </p>
    `;
}


/* =========================================
   4. SUMMARY CARDS
========================================= */

function renderSummaryCards(summary) {
    const cards = [
        {
            label: "Total Complaints",
            value: summary.total_complaints,
            icon: "bi-clipboard-data",
            color: "blue"
        },
        {
            label: "Open Complaints",
            value: summary.open_complaints,
            icon: "bi-hourglass-split",
            color: "orange"
        },
        {
            label: "Closed Complaints",
            value: summary.closed_complaints,
            icon: "bi-check-circle",
            color: "green"
        },
        {
            label: "Repeat Complaints",
            value: summary.repeat_complaints,
            icon: "bi-arrow-repeat",
            color: "purple"
        },
        {
            label: "Accepted Complaints",
            value: summary.accepted_complaints,
            icon: "bi-check-circle-fill",
            color: "teal"
        },
        {
            label: "Rejected Complaints",
            value: summary.rejected_complaints,
            icon: "bi-x-circle",
            color: "red"
        }
    ];

    return `
        <div class="row g-3">

            ${cards.map(card => `
                <div class="col-xl-4 col-md-6">
                    <div class="report-stat-card">

                        <div class="d-flex align-items-center gap-3">

                            <div class="summary-icon ${card.color}">
                                <i class="bi ${card.icon}"></i>
                            </div>

                            <div>
                                <p>${card.label}</p>
                                <h4>${Number(card.value ?? 0)}</h4>
                            </div>

                        </div>

                    </div>
                </div>
            `).join("")}

        </div>
    `;
}


/* =========================================
   5. BREAKDOWN TABLES
========================================= */

function renderBreakdown(title, rows, labelKey) {
    if (!Array.isArray(rows) || rows.length === 0) {
        return `
            <div class="dashboard-panel">
                <h6>${escapeHTML(title)}</h6>
                <p class="text-secondary small mb-0">
                    No records found.
                </p>
            </div>
        `;
    }

    return `
        <div class="dashboard-panel">

            <div class="panel-heading">
                <h6>${escapeHTML(title)}</h6>
            </div>

            <div class="table-responsive">

                <table class="table report-table">

                    <thead>
                        <tr>
                            <th>Category</th>
                            <th class="text-end">Complaint Count</th>
                        </tr>
                    </thead>

                    <tbody>

                        ${rows.map(row => `
                            <tr>
                                <td>
                                    ${escapeHTML(formatLabel(row[labelKey]))}
                                </td>

                                <td class="text-end fw-semibold">
                                    ${Number(row.complaint_count ?? 0)}
                                </td>
                            </tr>
                        `).join("")}

                    </tbody>

                </table>

            </div>

        </div>
    `;
}


/* =========================================
   6. DOWNLOAD SUMMARY PDF
========================================= */

function downloadSummaryPDF() {
    downloadSummaryFile("pdf");
}


/* =========================================
   7. DOWNLOAD SUMMARY EXCEL
========================================= */

function downloadSummaryExcel() {
    downloadSummaryFile("excel");
}


async function downloadSummaryFile(format) {
    hideMessage();

    const queryString = getDateFilters();

    if (queryString === null) {
        return;
    }

    const isPDF = format === "pdf";

    const button = document.getElementById(
        isPDF ? "pdfButton" : "excelButton"
    );

    const originalText = isPDF
        ? "Download PDF"
        : "Download Excel";

    setButtonLoading(button, true, originalText);

    try {
        let url = `${API_BASE_URL}/complaint-summary/${format}`;

        if (queryString) {
            url += `?${queryString}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));

            throw new Error(
                errorData.detail || `Unable to generate ${format.toUpperCase()} report.`
            );
        }

        const blob = await response.blob();

        const downloadUrl = window.URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = downloadUrl;
        link.download = isPDF
            ? "complaint_summary_report.pdf"
            : "complaint_summary_report.xlsx";

        document.body.appendChild(link);
        link.click();

        link.remove();

        window.URL.revokeObjectURL(downloadUrl);

        showMessage(
            `${format.toUpperCase()} report downloaded successfully.`,
            "success"
        );

    } catch (error) {
        showMessage(error.message, "danger");

    } finally {
        setButtonLoading(button, false, originalText);
    }
}


/* =========================================
   8. DOWNLOAD INDIVIDUAL COMPLAINT REPORT
========================================= */

async function downloadIndividualComplaintReport() {
    hideMessage();

    const complaintInput = document.getElementById(
        "individualComplaintNumber"
    );

    const complaintNumber = complaintInput
        ? complaintInput.value.trim()
        : "";

    if (!complaintNumber) {
        showMessage("Please enter a complaint number.", "warning");
        return;
    }

    const button = document.getElementById("individualReportButton");

    const originalText = "Download Individual Report";

    setButtonLoading(button, true, originalText);

    try {
        const url =
            `${API_BASE_URL}/complaints/` +
            `${encodeURIComponent(complaintNumber)}/pdf`;

        const response = await fetch(url);

        if (!response.ok) {
            let errorMessage = "Unable to generate individual complaint report.";

            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch {
                // Keep the default error message.
            }

            throw new Error(errorMessage);
        }

        const blob = await response.blob();

        const downloadUrl = window.URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = downloadUrl;
        link.download = `complaint_report_${complaintNumber}.pdf`;

        document.body.appendChild(link);
        link.click();

        link.remove();

        window.URL.revokeObjectURL(downloadUrl);

        showMessage(
            "Individual complaint report downloaded successfully.",
            "success"
        );

    } catch (error) {
        showMessage(error.message, "danger");

    } finally {
        setButtonLoading(button, false, originalText);
    }
}


/* =========================================
   9. DOWNLOAD INDIVIDUAL REJECTION REPORT
========================================= */

async function downloadRejectionReport() {
    hideMessage();

    const complaintNumber = document
        .getElementById("complaintNumber")
        .value
        .trim();

    if (!complaintNumber) {
        showMessage("Please enter a complaint number.", "warning");
        return;
    }

    const button = document.getElementById("rejectionButton");

    const originalText = "Download Rejection PDF";

    setButtonLoading(button, true, originalText);

    try {
        const url =
            `${API_BASE_URL}/complaints/` +
            `${encodeURIComponent(complaintNumber)}/rejection.pdf`;

        const response = await fetch(url);

        if (!response.ok) {
            let errorMessage = "Unable to generate rejection report.";

            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch {
                // Keep the default error message.
            }

            throw new Error(errorMessage);
        }

        const blob = await response.blob();

        const downloadUrl = window.URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = downloadUrl;
        link.download = `rejection_report_${complaintNumber}.pdf`;

        document.body.appendChild(link);
        link.click();

        link.remove();

        window.URL.revokeObjectURL(downloadUrl);

        showMessage(
            "Rejection report downloaded successfully.",
            "success"
        );

    } catch (error) {
        showMessage(error.message, "danger");

    } finally {
        setButtonLoading(button, false, originalText);
    }
}
