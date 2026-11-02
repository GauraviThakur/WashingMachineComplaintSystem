
/* =========================================
   BULK UPLOAD PAGE
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const bulkUploadForm = document.getElementById("bulkUploadForm");
    const bulkFileInput = document.getElementById("bulkFile");
    const uploadedByInput = document.getElementById("uploadedBy");

    const selectedFileInfo = document.getElementById("selectedFileInfo");
    const selectedFileName = document.getElementById("selectedFileName");

    const uploadButton = document.getElementById("uploadBulkFileBtn");
    const resetButton = document.getElementById("resetBulkUploadBtn");

    const uploadMessage = document.getElementById("bulkUploadMessage");

    const summarySection = document.getElementById(
        "bulkRequestSummarySection"
    );

    const rowResultsSection = document.getElementById(
        "bulkRowResultsSection"
    );

    const rowResultsTable = document.getElementById(
        "bulkRowResultsTable"
    );

    const downloadReportButton = document.getElementById(
        "downloadBulkReportBtn"
    );

    const MAX_FILE_SIZE = 10 * 1024 * 1024;

    let currentBulkRequestId = null;


    /* =========================================
       FILE SELECTION
    ========================================= */

    bulkFileInput.addEventListener("change", () => {

        const file = bulkFileInput.files[0];

        selectedFileInfo.classList.add("d-none");

        if (!file) {
            return;
        }

        const extension = file.name
            .split(".")
            .pop()
            .toLowerCase();

        if (!["csv", "xlsx"].includes(extension)) {
            bulkFileInput.value = "";

            showUploadMessage(
                "Unsupported file format. Please select a CSV or XLSX file.",
                "danger"
            );

            return;
        }

        if (file.size > MAX_FILE_SIZE) {
            bulkFileInput.value = "";

            showUploadMessage(
                "File size must not exceed 10 MB.",
                "danger"
            );

            return;
        }

        selectedFileName.textContent =
            `${file.name} (${formatFileSize(file.size)})`;

        selectedFileInfo.classList.remove("d-none");

        clearUploadMessage();
    });


    /* =========================================
       BULK UPLOAD FORM SUBMISSION
    ========================================= */

    bulkUploadForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        const file = bulkFileInput.files[0];
        const uploadedBy = uploadedByInput.value.trim();

        clearUploadMessage();

        if (!file) {
            showUploadMessage(
                "Please select a CSV or Excel file.",
                "danger"
            );
            return;
        }

        if (!uploadedBy) {
            showUploadMessage(
                "Please enter the employee name in Uploaded By.",
                "danger"
            );
            return;
        }

        const extension = file.name
            .split(".")
            .pop()
            .toLowerCase();

        if (!["csv", "xlsx"].includes(extension)) {
            showUploadMessage(
                "Unsupported file format. Please select a CSV or XLSX file.",
                "danger"
            );
            return;
        }

        if (file.size > MAX_FILE_SIZE) {
            showUploadMessage(
                "File size must not exceed 10 MB.",
                "danger"
            );
            return;
        }

        const formData = new FormData();

        formData.append("file", file);
        formData.append("uploaded_by", uploadedBy);

        setUploadLoading(true);

        try {

            const response = await apiRequest(
                "/bulk-requests/upload",
                {
                    method: "POST",
                    body: formData
                }
            );

            displayBulkRequestSummary(
                response.bulk_request
            );

            displayRowResults(
                response.row_results
            );

            currentBulkRequestId =
                response.bulk_request.bulk_request_id;

            showUploadMessage(
                response.message || "Bulk upload completed.",
                "success"
            );

            showNotification(
                "Bulk upload processing completed.",
                "success"
            );

        } catch (error) {

            console.error("Bulk upload failed:", error);

            showUploadMessage(
                error.message || "Unable to process the uploaded file.",
                "danger"
            );

        } finally {

            setUploadLoading(false);

        }

    });


    /* =========================================
       DISPLAY BULK REQUEST SUMMARY
    ========================================= */

    function displayBulkRequestSummary(request) {

        if (!request) {
            return;
        }

        document.getElementById("bulkTotalRows").textContent =
            request.total_rows ?? 0;

        document.getElementById("bulkValidRows").textContent =
            request.valid_rows ?? 0;

        document.getElementById("bulkInvalidRows").textContent =
            request.invalid_rows ?? 0;

        document.getElementById("bulkRequestId").textContent =
            request.bulk_request_id ?? "-";

        document.getElementById("bulkSourceFile").textContent =
            request.source_file_name || "-";

        document.getElementById("bulkUploadedBy").textContent =
            request.uploaded_by || "-";

        document.getElementById("bulkRequestStatus").textContent =
            request.request_status || "-";

        document.getElementById("bulkUploadedAt").textContent =
            formatDateTime(request.uploaded_at);

        summarySection.classList.remove("d-none");

    }


    /* =========================================
       DISPLAY ROW PROCESSING RESULTS
    ========================================= */

    function displayRowResults(results) {

        rowResultsTable.replaceChildren();

        if (!Array.isArray(results) || results.length === 0) {

            const row = document.createElement("tr");
            const cell = document.createElement("td");

            cell.colSpan = 4;
            cell.className = "text-center text-muted";
            cell.textContent = "No row results available.";

            row.appendChild(cell);
            rowResultsTable.appendChild(row);

            rowResultsSection.classList.remove("d-none");

            return;
        }

        results.forEach(result => {

            const row = document.createElement("tr");

            // File row number
            const rowNumberCell = document.createElement("td");
            rowNumberCell.textContent =
                result.row_number ?? "-";

            row.appendChild(rowNumberCell);


            // Processing status
            const statusCell = document.createElement("td");
            const statusBadge = document.createElement("span");

            statusBadge.className =
                result.status === "PROCESSED"
                    ? "badge bg-success"
                    : "badge bg-danger";

            statusBadge.textContent =
                result.status || "UNKNOWN";

            statusCell.appendChild(statusBadge);
            row.appendChild(statusCell);


            // Complaint number
            const complaintCell = document.createElement("td");

            complaintCell.textContent =
                result.complaint_number || "-";

            row.appendChild(complaintCell);


            // Validation errors
            const errorCell = document.createElement("td");

            if (
                Array.isArray(result.errors) &&
                result.errors.length > 0
            ) {

                const errorList = document.createElement("ul");

                errorList.className = "mb-0 ps-3";

                result.errors.forEach(error => {

                    const errorItem = document.createElement("li");

                    errorItem.textContent = error;

                    errorList.appendChild(errorItem);

                });

                errorCell.appendChild(errorList);

            } else {

                errorCell.textContent = "-";

            }

            row.appendChild(errorCell);

            rowResultsTable.appendChild(row);

        });

        rowResultsSection.classList.remove("d-none");

    }


    /* =========================================
       DOWNLOAD EXCEL REPORT
    ========================================= */

    downloadReportButton.addEventListener("click", async () => {

        if (!currentBulkRequestId) {
            showNotification(
                "No bulk request report is available.",
                "danger"
            );
            return;
        }

        const originalButtonContent =
            downloadReportButton.innerHTML;

        downloadReportButton.disabled = true;

        downloadReportButton.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2"></span>Downloading...';

        try {

            const response = await fetch(
                `${API_BASE_URL}/bulk-requests/${currentBulkRequestId}/report.xlsx`
            );

            if (!response.ok) {

                const responseText = await response.text();

                let errorData = null;

                try {
                    errorData = JSON.parse(responseText);
                } catch {
                    errorData = responseText;
                }

                let errorMessage =
                    `Report download failed with status ${response.status}.`;

                if (
                    errorData &&
                    typeof errorData === "object"
                ) {
                    errorMessage = extractErrorMessage(
                        errorData,
                        response.status
                    );
                } else if (
                    typeof errorData === "string" &&
                    errorData.trim()
                ) {
                    errorMessage = errorData;
                }

                throw new Error(errorMessage);

            }

            const reportBlob = await response.blob();

            const downloadUrl = URL.createObjectURL(reportBlob);

            const downloadLink = document.createElement("a");

            downloadLink.href = downloadUrl;

            downloadLink.download =
                `bulk_request_${currentBulkRequestId}_report.xlsx`;

            document.body.appendChild(downloadLink);

            downloadLink.click();

            downloadLink.remove();

            // Give the browser time to start the download
            // before releasing the temporary object URL.
            setTimeout(() => {
                URL.revokeObjectURL(downloadUrl);
            }, 1000);

            showNotification(
                "Excel report download initiated.",
                "success"
            );

        } catch (error) {

            console.error("Report download failed:", error);

            showNotification(
                error.message || "Unable to download the Excel report.",
                "danger"
            );

        } finally {

            downloadReportButton.disabled = false;

            downloadReportButton.innerHTML =
                originalButtonContent;

        }

    });


    /* =========================================
       RESET FORM
    ========================================= */

    resetButton.addEventListener("click", () => {

        bulkUploadForm.reset();

        selectedFileInfo.classList.add("d-none");

        clearUploadMessage();

        summarySection.classList.add("d-none");

        rowResultsSection.classList.add("d-none");

        rowResultsTable.replaceChildren();

        currentBulkRequestId = null;

    });


    /* =========================================
       HELPER FUNCTIONS
    ========================================= */

    function showUploadMessage(message, type) {

        uploadMessage.replaceChildren();

        const alert = document.createElement("div");

        alert.className = `alert alert-${type} mb-0`;

        alert.textContent = message;

        uploadMessage.appendChild(alert);

    }


    function clearUploadMessage() {

        uploadMessage.replaceChildren();

    }


    function setUploadLoading(isLoading) {

        uploadButton.disabled = isLoading;
        bulkFileInput.disabled = isLoading;
        uploadedByInput.disabled = isLoading;
        resetButton.disabled = isLoading;

        if (isLoading) {

            uploadButton.innerHTML =
                '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

        } else {

            uploadButton.innerHTML =
                '<i class="bi bi-cloud-arrow-up me-2"></i>Upload and Process';

        }

    }


    function formatFileSize(bytes) {

        if (bytes < 1024) {
            return `${bytes} bytes`;
        }

        if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
        }

        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;

    }


    function formatDateTime(dateValue) {

        if (!dateValue) {
            return "-";
        }

        const date = new Date(dateValue);

        if (Number.isNaN(date.getTime())) {
            return "-";
        }

        return date.toLocaleString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });

    }

});
