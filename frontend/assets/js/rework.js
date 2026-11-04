document.addEventListener("DOMContentLoaded", () => {
    const complaintNumberInput = document.getElementById("complaintNumber");
    const loadComplaintBtn = document.getElementById("loadComplaintBtn");

    const complaintDetailsSection = document.getElementById("complaintDetailsSection");
    const reworkFormSection = document.getElementById("reworkFormSection");
    const reworkHistorySection = document.getElementById("reworkHistorySection");
    const reworkResultSection = document.getElementById("reworkResultSection");

    const reworkForm = document.getElementById("reworkForm");
    const submitReworkBtn = document.getElementById("submitReworkBtn");

    let currentComplaint = null;

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[character]);
    }

    function showMessage(containerId, message, type = "danger") {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="alert alert-${type} mb-0" role="alert">
                ${escapeHtml(message)}
            </div>
        `;
    }

    function clearMessage(containerId) {
        document.getElementById(containerId).innerHTML = "";
    }

    function formatLabel(value) {
        if (!value) return "-";

        return String(value)
            .toLowerCase()
            .replaceAll("_", " ")
            .replace(/\b\w/g, character => character.toUpperCase());
    }

    function getComplaintObject(response) {
        return response?.complaint || response?.data?.complaint || response?.data || response;
    }

    function setComplaintDetails(complaint) {
        document.getElementById("detailComplaintNumber").value =
            complaint.complaint_number || "-";

        document.getElementById("detailSerialNumber").value =
            complaint.serial_number || complaint.machine_serial_number || "-";

        document.getElementById("detailModelNumber").value =
            complaint.model_number || complaint.machine_model || "-";

        document.getElementById("detailCustomerName").value =
            complaint.customer_name || "-";

        document.getElementById("detailDealerEmail").value =
            complaint.dealer_email || "-";

        document.getElementById("detailComplaintStatus").value =
            formatLabel(complaint.complaint_status || complaint.status);

        document.getElementById("detailReportedIssue").value =
            complaint.reported_issue || "-";
    }

    function getComplaintStatus(complaint) {
        return complaint?.complaint_status || complaint?.status || "";
    }

    function canRecordRework(complaint) {
        const status = getComplaintStatus(complaint);
        return status === "ASSIGNED" || status === "UNDER_REWORK";
    }

    function hideWorkflowSections() {
        complaintDetailsSection.classList.add("d-none");
        reworkFormSection.classList.add("d-none");
        reworkHistorySection.classList.add("d-none");
        reworkResultSection.classList.add("d-none");
    }

    function renderReworkHistory(response) {
        const historyBody = document.getElementById("reworkHistoryBody");

        const attempts =
            response?.rework_attempts ||
            response?.rework_history ||
            response?.attempts ||
            response?.data?.rework_attempts ||
            response?.data?.rework_history ||
            [];

        if (!Array.isArray(attempts) || attempts.length === 0) {
            historyBody.innerHTML = `
                <p class="text-muted mb-0">No previous rework attempts found for this complaint.</p>
            `;
            reworkHistorySection.classList.remove("d-none");
            return;
        }

        const rows = attempts.map((attempt, index) => {
            const attemptNumber =
                attempt.attempt_number ||
                attempt.rework_attempt_number ||
                index + 1;

            return `
                <tr>
                    <td>${escapeHtml(attemptNumber)}</td>
                    <td>${escapeHtml(attempt.performed_by || "-")}</td>
                    <td>${escapeHtml(formatLabel(attempt.rework_result))}</td>
                    <td>${escapeHtml(attempt.rework_action || "-")}</td>
                    <td>${escapeHtml(attempt.parts_replaced || "-")}</td>
                    <td>${escapeHtml(attempt.requires_testing === true ? "Yes" : attempt.requires_testing === false ? "No" : "-")}</td>
                    <td>${escapeHtml(attempt.created_at || attempt.performed_at || attempt.rework_date || "-")}</td>
                </tr>
                ${attempt.rework_notes ? `
                    <tr>
                        <td colspan="7" class="text-muted">
                            <strong>Notes:</strong> ${escapeHtml(attempt.rework_notes)}
                        </td>
                    </tr>
                ` : ""}
            `;
        }).join("");

        historyBody.innerHTML = `
            <div class="table-responsive">
                <table class="table table-bordered table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Attempt</th>
                            <th>Performed By</th>
                            <th>Result</th>
                            <th>Rework Action</th>
                            <th>Parts Replaced</th>
                            <th>Testing Required</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;

        reworkHistorySection.classList.remove("d-none");
    }

    async function loadReworkHistory(complaintNumber) {
        try {
            const response = await apiRequest(
                `/rework/${encodeURIComponent(complaintNumber)}`
            );

            renderReworkHistory(response);
        } catch (error) {
            document.getElementById("reworkHistoryBody").innerHTML = `
                <div class="alert alert-warning mb-0">
                    Unable to load rework history: ${escapeHtml(error.message)}
                </div>
            `;
            reworkHistorySection.classList.remove("d-none");
        }
    }

    async function loadComplaint() {
        const complaintNumber = complaintNumberInput.value.trim();

        clearMessage("pageMessage");
        clearMessage("reworkMessage");
        hideWorkflowSections();
        currentComplaint = null;

        if (!complaintNumber) {
            showMessage("pageMessage", "Please enter a complaint number.");
            return;
        }

        loadComplaintBtn.disabled = true;
        loadComplaintBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Loading...
        `;

        try {
            const response = await apiRequest(
                `/complaints/${encodeURIComponent(complaintNumber)}`
            );

            const complaint = getComplaintObject(response);

            if (!complaint || !complaint.complaint_number) {
                throw new Error("Complaint details could not be retrieved.");
            }

            currentComplaint = complaint;
            setComplaintDetails(complaint);
            complaintDetailsSection.classList.remove("d-none");

            if (canRecordRework(complaint)) {
                reworkFormSection.classList.remove("d-none");
            } else {
                showMessage(
                    "pageMessage",
                    `Rework cannot be recorded because the complaint status is ${formatLabel(getComplaintStatus(complaint))}. Rework is allowed only for ASSIGNED or UNDER_REWORK complaints.`,
                    "warning"
                );
            }

            await loadReworkHistory(complaintNumber);

        } catch (error) {
            showMessage("pageMessage", error.message);
        } finally {
            loadComplaintBtn.disabled = false;
            loadComplaintBtn.innerHTML = `
                <i class="bi bi-search me-2"></i>Load Complaint
            `;
        }
    }

    function showReworkResult(response) {
        const result = response?.data || response;

        const currentStatus =
            result?.current_status ||
            result?.complaint_status ||
            result?.new_status ||
            "-";

        const resultType = result?.rework_result || "";

        let nextStep = "Review the complaint's updated status before proceeding.";

        if (resultType === "COMPLETED" && result?.requires_testing === true) {
            nextStep = "The complaint should proceed to Testing.";
        } else if (resultType === "UNSUCCESSFUL") {
            nextStep = "The unsuccessful rework attempt has been recorded. Review the complaint's updated status and follow the Quality Decision workflow when applicable.";
        } else if (resultType === "PARTIALLY_COMPLETED") {
            nextStep = "The partial rework attempt has been recorded. Follow the complaint's updated status for the next action.";
        } else if (resultType === "COMPLETED" && result?.requires_testing === false) {
            nextStep = "Further testing was not requested. Review the updated complaint status for the next workflow action.";
        }

        document.getElementById("reworkResultBody").innerHTML = `
            <div class="alert alert-success">
                <h6><i class="bi bi-check-circle me-2"></i>Rework recorded successfully</h6>
                <p class="mb-1"><strong>Result:</strong> ${escapeHtml(formatLabel(resultType))}</p>
                <p class="mb-1"><strong>Current Status:</strong> ${escapeHtml(formatLabel(currentStatus))}</p>
                <p class="mb-0">${escapeHtml(nextStep)}</p>
            </div>
        `;

        reworkResultSection.classList.remove("d-none");
    }

    loadComplaintBtn.addEventListener("click", loadComplaint);

    complaintNumberInput.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            loadComplaint();
        }
    });

    reworkForm.addEventListener("submit", async event => {
        event.preventDefault();

        clearMessage("reworkMessage");

        if (!currentComplaint) {
            showMessage("reworkMessage", "Load a complaint before recording rework.");
            return;
        }

        if (!canRecordRework(currentComplaint)) {
            showMessage(
                "reworkMessage",
                "This complaint is not in a status that allows rework."
            );
            return;
        }

        const payload = {
            complaint_number: currentComplaint.complaint_number,
            performed_by: document.getElementById("performedBy").value.trim(),
            rework_action: document.getElementById("reworkAction").value.trim(),
            parts_replaced: document.getElementById("partsReplaced").value.trim() || null,
            rework_result: document.getElementById("reworkResult").value,
            requires_testing: document.getElementById("requiresTesting").value === "true",
            rework_notes: document.getElementById("reworkNotes").value.trim() || null
        };

        if (payload.performed_by.length < 2) {
            showMessage("reworkMessage", "Performed By must contain at least 2 characters.");
            return;
        }

        if (payload.rework_action.length < 3) {
            showMessage("reworkMessage", "Rework Action must contain at least 3 characters.");
            return;
        }

        submitReworkBtn.disabled = true;
        submitReworkBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Submitting...
        `;

        try {
            const response = await apiRequest("/rework/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            showReworkResult(response);

            reworkForm.reset();
            document.getElementById("requiresTesting").value = "true";

            showMessage(
                "reworkMessage",
                "Rework attempt saved successfully.",
                "success"
            );

            // Refresh complaint status and rework history after saving.
            await loadComplaint();

        } catch (error) {
            showMessage("reworkMessage", error.message);
        } finally {
            submitReworkBtn.disabled = false;
            submitReworkBtn.innerHTML = `
                <i class="bi bi-check-circle me-2"></i>Submit Rework
            `;
        }
    });

    reworkForm.addEventListener("reset", () => {
        setTimeout(() => {
            clearMessage("reworkMessage");
        }, 0);
    });
});