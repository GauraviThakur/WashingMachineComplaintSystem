
/* =========================================
   BULK REQUEST TRACKING
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const searchForm = document.getElementById("bulkTrackingSearchForm");
    const searchInput = document.getElementById("bulkTrackingSearch");
    const searchButton = document.getElementById("bulkTrackingSearchBtn");
    const searchMessage = document.getElementById("bulkTrackingSearchMessage");

    const resultsSection = document.getElementById("bulkTrackingResultsSection");
    const resultsCount = document.getElementById("bulkTrackingResultsCount");
    const resultsTable = document.getElementById("bulkTrackingResultsTable");

    const detailsSection = document.getElementById("bulkTrackingDetailsSection");
    const rowsTable = document.getElementById("bulkTrackingRowsTable");

    const downloadButton = document.getElementById(
        "downloadBulkTrackingReportBtn"
    );

    let currentBulkRequestId = null;


    /* =========================================
       HELPER FUNCTIONS
    ========================================= */

    function escapeHTML(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    function formatValue(value) {
        if (value === null || value === undefined || value === "") {
            return "--";
        }

        return escapeHTML(value);
    }


    function formatDate(value) {
        if (!value) {
            return "--";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return formatValue(value);
        }

        return date.toLocaleString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }


    function showMessage(message, type = "info") {
        const alertClasses = {
            success: "alert-success",
            error: "alert-danger",
            warning: "alert-warning",
            info: "alert-info"
        };

        searchMessage.innerHTML = `
            <div class="alert ${alertClasses[type] || "alert-info"} mb-0">
                ${escapeHTML(message)}
            </div>
        `;
    }


    function getStatusClass(status) {
        const value = String(status || "").toUpperCase();

        if (
            ["PROCESSED", "COMPLETED", "CLOSED", "APPROVED"].includes(value)
        ) {
            return "success";
        }

        if (
            ["INVALID", "FAILED", "REJECTED", "COMPLETED_WITH_ERRORS"].includes(value)
        ) {
            return "danger";
        }

        if (
            value.includes("PARTIAL") ||
            ["IN_PROGRESS", "PROCESSING", "PENDING"].includes(value)
        ) {
            return "warning";
        }

        return "secondary";
    }


    function statusBadge(status) {
        return `
            <span class="badge bg-${getStatusClass(status)}">
                ${formatValue(status)}
            </span>
        `;
    }


    function getErrorText(errors) {
        if (Array.isArray(errors)) {
            return errors.length
                ? errors.map(error => escapeHTML(error)).join("<br>")
                : "--";
        }

        return formatValue(errors);
    }


    /* =========================================
       RESET RESULTS
    ========================================= */

    function resetResults() {
        resultsSection.classList.add("d-none");
        detailsSection.classList.add("d-none");

        resultsTable.innerHTML = "";
        rowsTable.innerHTML = "";

        currentBulkRequestId = null;
    }


    /* =========================================
       DISPLAY SEARCH RESULT
    ========================================= */

    function displaySearchResult(request) {

        const requestId = request.bulk_request_id;

        resultsTable.innerHTML = `
            <tr>
                <td><strong>${formatValue(requestId)}</strong></td>
                <td>${formatValue(request.source_file_name)}</td>
                <td>${formatValue(request.uploaded_by)}</td>
                <td>${formatValue(request.total_rows)}</td>
                <td>${statusBadge(request.request_status)}</td>
                <td>${statusBadge(request.complaint_completion_status)}</td>
                <td>
                    <button
                        type="button"
                        class="btn btn-sm btn-primary view-bulk-request-btn"
                        data-request-id="${escapeHTML(requestId)}"
                    >
                        <i class="bi bi-eye me-1"></i>
                        View Details
                    </button>
                </td>
            </tr>
        `;

        resultsCount.textContent = "1 matching bulk request found.";
        resultsSection.classList.remove("d-none");
    }


    /* =========================================
       DISPLAY REQUEST SUMMARY
    ========================================= */

    function displayRequestSummary(request) {

        document.getElementById("trackingTotalRows").textContent =
            request.total_rows ?? 0;

        document.getElementById("trackingValidRows").textContent =
            request.valid_rows ?? 0;

        document.getElementById("trackingInvalidRows").textContent =
            request.invalid_rows ?? 0;

        document.getElementById("trackingRequestId").textContent =
            request.bulk_request_id ?? "--";

        document.getElementById("trackingSourceFile").textContent =
            request.source_file_name ?? "--";

        document.getElementById("trackingUploadedBy").textContent =
            request.uploaded_by ?? "--";

        document.getElementById("trackingRequestStatus").innerHTML =
            statusBadge(request.request_status);

        document.getElementById("trackingCompletionStatus").innerHTML =
            statusBadge(request.complaint_completion_status);

        document.getElementById("trackingUploadedAt").textContent =
            formatDate(request.uploaded_at);

        document.getElementById("trackingProcessedAt").textContent =
            formatDate(request.completed_at);

        document.getElementById("trackingComplaintsCompletedAt").textContent =
            formatDate(request.complaints_completed_at);
    }


    /* =========================================
       DISPLAY INDIVIDUAL ROW DETAILS
    ========================================= */

    function displayRows(rows) {

        if (!Array.isArray(rows) || rows.length === 0) {
            rowsTable.innerHTML = `
                <tr>
                    <td colspan="10" class="text-center">
                        No uploaded row details found.
                    </td>
                </tr>
            `;

            return;
        }

        rowsTable.innerHTML = rows.map(row => {

            const validationStatus = row.validation_status || "--";

            const complaintStatus = row.complaint_status || "--";

            const errors = getErrorText(row.validation_errors);

            return `
                <tr>
                    <td>${formatValue(row.row_number)}</td>

                    <td>${formatValue(row.row_data?.serial_number)}</td>

                    <td>${formatValue(row.row_data?.customer_name)}</td>

                    <td>${formatValue(
                        row.registered_reported_issue ||
                        row.row_data?.reported_issue
                    )}</td>

                    <td>${formatValue(row.issue_type_name)}</td>

                    <td>${statusBadge(validationStatus)}</td>

                    <td>${formatValue(row.complaint_number)}</td>

                    <td>${statusBadge(complaintStatus)}</td>

                    <td>${formatValue(row.priority)}</td>

                    <td>${errors}</td>
                </tr>
            `;

        }).join("");
    }


    /* =========================================
       LOAD BULK REQUEST DETAILS
    ========================================= */

    async function loadBulkRequestDetails(requestId) {

        try {

            showMessage("Loading bulk request details...", "info");

            detailsSection.classList.add("d-none");

            const response = await apiRequest(
                `/bulk-requests/${encodeURIComponent(requestId)}`
            );

            const request = response.bulk_request;
            const rows = response.rows || [];

            if (!request || !request.bulk_request_id) {
                throw new Error("Bulk request details were not returned correctly.");
            }

            currentBulkRequestId = request.bulk_request_id;

            displaySearchResult(request);
            displayRequestSummary(request);
            displayRows(rows);

            detailsSection.classList.remove("d-none");

            showMessage(
                `Bulk request ${currentBulkRequestId} loaded successfully.`,
                "success"
            );

        } catch (error) {

            detailsSection.classList.add("d-none");

            showMessage(
                error.message || "Unable to load bulk request details.",
                "error"
            );
        }
    }


    /* =========================================
       SEARCH BULK REQUEST
    ========================================= */

    searchForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        const searchValue = searchInput.value.trim();

        if (!searchValue) {
            showMessage("Please enter a Bulk Request ID.", "warning");
            return;
        }

        resetResults();

        if (!/^\d+$/.test(searchValue)) {
            showMessage(
                "Please enter a numeric Bulk Request ID. Filename search is not yet supported by the backend.",
                "warning"
            );

            return;
        }

        searchButton.disabled = true;

        searchButton.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Searching...
        `;

        try {
            await loadBulkRequestDetails(searchValue);

        } finally {

            searchButton.disabled = false;

            searchButton.innerHTML = `
                <i class="bi bi-search me-2"></i>
                Search
            `;
        }
    });


    /* =========================================
       VIEW REQUEST DETAILS
    ========================================= */

    resultsTable.addEventListener("click", async (event) => {

        const button = event.target.closest(".view-bulk-request-btn");

        if (!button) {
            return;
        }

        const requestId = button.dataset.requestId;

        if (!requestId) {
            return;
        }

        await loadBulkRequestDetails(requestId);

        detailsSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    });


    /* =========================================
       DOWNLOAD EXCEL REPORT
    ========================================= */

    downloadButton.addEventListener("click", () => {

        if (!currentBulkRequestId) {
            showMessage(
                "Please load a bulk request before downloading its report.",
                "warning"
            );

            return;
        }

        const reportUrl =
            `${API_BASE_URL}/bulk-requests/` +
            `${encodeURIComponent(currentBulkRequestId)}/report.xlsx`;

        window.location.href = reportUrl;
    });

});
