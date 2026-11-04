
document.addEventListener("DOMContentLoaded", () => {
    const complaintNumberInput = document.getElementById("complaintNumber");
    const loadComplaintBtn = document.getElementById("loadComplaintBtn");

    const complaintDetailsSection = document.getElementById("complaintDetailsSection");
    const testingFormSection = document.getElementById("testingFormSection");
    const testHistorySection = document.getElementById("testHistorySection");
    const testResultSection = document.getElementById("testResultSection");

    const testingForm = document.getElementById("testingForm");
    const submitTestBtn = document.getElementById("submitTestBtn");

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
        document.getElementById(containerId).innerHTML = `
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

    function getComplaintStatus(complaint) {
        return complaint?.complaint_status || complaint?.status || "";
    }

    function canRecordTesting(complaint) {
        return getComplaintStatus(complaint) === "UNDER_TESTING";
    }

    function hideWorkflowSections() {
        complaintDetailsSection.classList.add("d-none");
        testingFormSection.classList.add("d-none");
        testHistorySection.classList.add("d-none");
        testResultSection.classList.add("d-none");
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
            formatLabel(getComplaintStatus(complaint));

        document.getElementById("detailReportedIssue").value =
            complaint.reported_issue || "-";
    }

    function renderTestHistory(response) {
        const historyBody = document.getElementById("testHistoryBody");

        const attempts =
            response?.test_attempts ||
            response?.data?.test_attempts ||
            [];

        if (!Array.isArray(attempts) || attempts.length === 0) {
            historyBody.innerHTML = `
                <p class="text-muted mb-0">
                    No previous testing attempts found for this complaint.
                </p>
            `;
            testHistorySection.classList.remove("d-none");
            return;
        }

        const rows = attempts.map(attempt => `
            <tr>
                <td>${escapeHtml(attempt.test_number ?? "-")}</td>
                <td>${escapeHtml(attempt.tested_by || "-")}</td>
                <td>${escapeHtml(attempt.test_type || "-")}</td>
                <td>
                    <span class="badge ${attempt.test_result === "PASS" ? "bg-success" : "bg-danger"}">
                        ${escapeHtml(attempt.test_result || "-")}
                    </span>
                </td>
                <td>${escapeHtml(attempt.test_observations || "-")}</td>
                <td>${escapeHtml(attempt.tested_at || attempt.created_at || "-")}</td>
            </tr>
            ${attempt.test_notes ? `
                <tr>
                    <td colspan="6" class="text-muted">
                        <strong>Notes:</strong> ${escapeHtml(attempt.test_notes)}
                    </td>
                </tr>
            ` : ""}
        `).join("");

        historyBody.innerHTML = `
            <div class="table-responsive">
                <table class="table table-bordered table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Attempt</th>
                            <th>Tested By</th>
                            <th>Test Type</th>
                            <th>Result</th>
                            <th>Observations</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;

        testHistorySection.classList.remove("d-none");
    }

    async function loadTestHistory(complaintNumber) {
        try {
            const response = await apiRequest(
                `/testing/${encodeURIComponent(complaintNumber)}`
            );

            renderTestHistory(response);
        } catch (error) {
            document.getElementById("testHistoryBody").innerHTML = `
                <div class="alert alert-warning mb-0">
                    Unable to load testing history: ${escapeHtml(error.message)}
                </div>
            `;
            testHistorySection.classList.remove("d-none");
        }
    }

    function showTestResult(response) {
        const result = response?.data || response;

        const currentStatus =
            result?.complaint_status ||
            result?.current_status ||
            "-";

        const testRecord = result?.test_record || {};
        const testOutcome =
            testRecord?.test_result ||
            result?.test_result ||
            "";

        let nextStep = "Review the complaint's updated status before proceeding.";

        if (testOutcome === "PASS") {
            nextStep = "The test passed. The complaint is awaiting the next quality workflow action.";
        } else if (testOutcome === "FAIL") {
            nextStep = "The test failed. Review the updated complaint status and follow the corrective rework process.";
        }

        document.getElementById("testResultBody").innerHTML = `
            <div class="alert alert-success mb-0">
                <h6>
                    <i class="bi bi-check-circle me-2"></i>
                    Test result recorded successfully
                </h6>
                <p class="mb-1">
                    <strong>Test Result:</strong>
                    ${escapeHtml(testOutcome || "-")}
                </p>
                <p class="mb-1">
                    <strong>Current Status:</strong>
                    ${escapeHtml(formatLabel(currentStatus))}
                </p>
                <p class="mb-0">${escapeHtml(nextStep)}</p>
            </div>
        `;

        testResultSection.classList.remove("d-none");
    }

    async function loadComplaint() {
        const complaintNumber = complaintNumberInput.value.trim();

        clearMessage("pageMessage");
        clearMessage("testingMessage");
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

            if (canRecordTesting(complaint)) {
                testingFormSection.classList.remove("d-none");
            } else {
                showMessage(
                    "pageMessage",
                    `Testing cannot be recorded because the complaint status is ${formatLabel(getComplaintStatus(complaint))}. Testing is allowed only for UNDER_TESTING complaints.`,
                    "warning"
                );
            }

            await loadTestHistory(complaintNumber);

        } catch (error) {
            showMessage("pageMessage", error.message);
        } finally {
            loadComplaintBtn.disabled = false;
            loadComplaintBtn.innerHTML = `
                <i class="bi bi-search me-2"></i>Load Complaint
            `;
        }
    }

    loadComplaintBtn.addEventListener("click", loadComplaint);

    complaintNumberInput.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            loadComplaint();
        }
    });

    testingForm.addEventListener("submit", async event => {
        event.preventDefault();

        clearMessage("testingMessage");

        if (!currentComplaint) {
            showMessage("testingMessage", "Load a complaint before recording a test.");
            return;
        }

        if (!canRecordTesting(currentComplaint)) {
            showMessage(
                "testingMessage",
                "This complaint is not currently eligible for testing."
            );
            return;
        }

        const payload = {
            complaint_number: currentComplaint.complaint_number,
            tested_by: document.getElementById("testedBy").value.trim(),
            test_type: document.getElementById("testType").value.trim(),
            test_result: document.getElementById("testResult").value,
            test_observations: document.getElementById("testObservations").value.trim(),
            test_notes: document.getElementById("testNotes").value.trim() || null
        };

        if (payload.tested_by.length < 2 || payload.test_type.length < 2 ||
            payload.test_observations.length < 3) {
            showMessage("testingMessage", "Please complete all required fields correctly.");
            return;
        }

        submitTestBtn.disabled = true;
        submitTestBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Submitting...
        `;

        try {
            const response = await apiRequest("/testing/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            showTestResult(response);

            testingForm.reset();

            showMessage(
                "testingMessage",
                "Test result saved successfully.",
                "success"
            );

            // Refresh complaint details and history without hiding the result.
            const refreshedResponse = await apiRequest(
                `/complaints/${encodeURIComponent(currentComplaint.complaint_number)}`
            );

            currentComplaint = getComplaintObject(refreshedResponse);
            setComplaintDetails(currentComplaint);

            if (!canRecordTesting(currentComplaint)) {
                testingFormSection.classList.add("d-none");
            }

            await loadTestHistory(currentComplaint.complaint_number);

        } catch (error) {
            showMessage("testingMessage", error.message);
        } finally {
            submitTestBtn.disabled = false;
            submitTestBtn.innerHTML = `
                <i class="bi bi-check-circle me-2"></i>Submit Test Result
            `;
        }
    });

    testingForm.addEventListener("reset", () => {
        setTimeout(() => {
            clearMessage("testingMessage");
        }, 0);
    });
});
