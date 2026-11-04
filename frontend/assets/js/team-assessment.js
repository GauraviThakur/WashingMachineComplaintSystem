
document.addEventListener("DOMContentLoaded", () => {
    const pendingAssignmentsBody = document.getElementById("pendingAssignmentsBody");
    const pendingLoading = document.getElementById("pendingLoading");

    const complaintDetailsSection = document.getElementById("complaintDetailsSection");
    const assessmentFormSection = document.getElementById("assessmentFormSection");
    const assessmentResultSection = document.getElementById("assessmentResultSection");

    const assessmentForm = document.getElementById("assessmentForm");
    const submitAssessmentBtn = document.getElementById("submitAssessmentBtn");
    const refreshBtn = document.getElementById("refreshBtn");
    const cancelAssessmentBtn = document.getElementById("cancelAssessmentBtn");

    let selectedAssignment = null;

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

    function hideAssessmentSections() {
        complaintDetailsSection.classList.add("d-none");
        assessmentFormSection.classList.add("d-none");
        assessmentResultSection.classList.add("d-none");
    }

    function renderPendingAssignments(items) {
        if (!Array.isArray(items) || items.length === 0) {
            pendingAssignmentsBody.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-clipboard-check fs-1 text-muted"></i>
                    <h6 class="mt-3">No Pending Assessments</h6>
                    <p class="text-muted mb-0">
                        There are currently no complaints waiting for team assessment.
                    </p>
                </div>
            `;
            return;
        }

        const rows = items.map(item => `
            <tr>
                <td>${escapeHtml(item.complaint_number)}</td>
                <td>${escapeHtml(item.serial_number)}</td>
                <td>${escapeHtml(item.model_number)}</td>
                <td>${escapeHtml(item.team_name)}</td>
                <td>${escapeHtml(item.assigned_to || "Not specified")}</td>
                <td>${escapeHtml(formatLabel(item.priority))}</td>
                <td>
                    <button
                        type="button"
                        class="btn btn-sm btn-primary assess-btn"
                        data-assignment-id="${escapeHtml(item.assignment_id)}"
                    >
                        <i class="bi bi-clipboard2-pulse me-1"></i>Assess
                    </button>
                </td>
            </tr>
        `).join("");

        pendingAssignmentsBody.innerHTML = `
            <div class="table-responsive">
                <table class="table table-bordered table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Complaint Number</th>
                            <th>Serial Number</th>
                            <th>Model Number</th>
                            <th>Assigned Team</th>
                            <th>Assigned To</th>
                            <th>Priority</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <p class="text-muted mb-0">
                Total pending assessments: ${items.length}
            </p>
        `;

        pendingAssignmentsBody.querySelectorAll(".assess-btn").forEach(button => {
            button.addEventListener("click", () => {
                const assignmentId = Number(button.dataset.assignmentId);

                const assignment = items.find(
                    item => Number(item.assignment_id) === assignmentId
                );

                if (assignment) {
                    selectAssignment(assignment);
                }
            });
        });
    }

    async function loadPendingAssignments() {
        clearMessage("pageMessage");
        pendingLoading.classList.remove("d-none");
        pendingAssignmentsBody.innerHTML = "";

        refreshBtn.disabled = true;

        try {
            const response = await apiRequest("/team-assessments/pending");

            const result = response?.data || response;
            const items = result?.items || [];

            renderPendingAssignments(items);
        } catch (error) {
            pendingAssignmentsBody.innerHTML = "";
            showMessage("pageMessage", error.message);
        } finally {
            pendingLoading.classList.add("d-none");
            refreshBtn.disabled = false;
        }
    }

    function selectAssignment(assignment) {
        selectedAssignment = assignment;

        clearMessage("assessmentMessage");
        clearMessage("pageMessage");

        assessmentForm.reset();

        document.getElementById("detailComplaintNumber").value =
            assignment.complaint_number || "-";

        document.getElementById("detailSerialNumber").value =
            assignment.serial_number || "-";

        document.getElementById("detailModelNumber").value =
            assignment.model_number || "-";

        document.getElementById("detailCustomerName").value =
            assignment.customer_name || "-";

        document.getElementById("detailTeamName").value =
            assignment.team_name || "-";

        document.getElementById("detailAssignedTo").value =
            assignment.assigned_to || "Not specified";

        document.getElementById("detailPriority").value =
            formatLabel(assignment.priority);

        document.getElementById("detailComplaintStatus").value =
            formatLabel(assignment.complaint_status);

        document.getElementById("detailReportedIssue").value =
            assignment.reported_issue || "-";

        assessmentResultSection.classList.add("d-none");
        complaintDetailsSection.classList.remove("d-none");
        assessmentFormSection.classList.remove("d-none");

        assessmentFormSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    function getNextStep(outcome) {
        const nextSteps = {
            REPAIR_REQUIRED:
                "The complaint will move to Rework for corrective action.",

            NO_REPAIR_REQUIRED:
                "The complaint will proceed directly to Testing.",

            FURTHER_INVESTIGATION_REQUIRED:
                "The complaint will return to Inspection for further investigation."
        };

        return nextSteps[outcome] || "Review the complaint's updated status.";
    }

    function showAssessmentResult(response) {
        const result = response?.data || response;
        const assessment = result?.assessment || {};

        const outcome =
            assessment.assessment_outcome ||
            document.getElementById("assessmentOutcome").value;

        const currentStatus =
            result?.complaint_status || "-";

        document.getElementById("assessmentResultBody").innerHTML = `
            <div class="alert alert-success mb-0">
                <h6>
                    <i class="bi bi-check-circle me-2"></i>
                    Assessment submitted successfully
                </h6>

                <p class="mb-1">
                    <strong>Complaint Number:</strong>
                    ${escapeHtml(result?.complaint_number || "-")}
                </p>

                <p class="mb-1">
                    <strong>Assessment Outcome:</strong>
                    ${escapeHtml(formatLabel(outcome))}
                </p>

                <p class="mb-1">
                    <strong>Current Status:</strong>
                    ${escapeHtml(formatLabel(currentStatus))}
                </p>

                <p class="mb-0">
                    ${escapeHtml(getNextStep(outcome))}
                </p>
            </div>
        `;

        assessmentResultSection.classList.remove("d-none");

        assessmentResultSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    refreshBtn.addEventListener("click", loadPendingAssignments);

    cancelAssessmentBtn.addEventListener("click", () => {
        selectedAssignment = null;
        assessmentForm.reset();
        hideAssessmentSections();
        clearMessage("assessmentMessage");
        clearMessage("pageMessage");
    });

    assessmentForm.addEventListener("submit", async event => {
        event.preventDefault();

        clearMessage("assessmentMessage");

        if (!selectedAssignment) {
            showMessage(
                "assessmentMessage",
                "Please select a pending complaint before submitting an assessment."
            );
            return;
        }

        const payload = {
            complaint_number: selectedAssignment.complaint_number,
            assessed_by: document.getElementById("assessedBy").value.trim(),
            assessment_findings: document.getElementById("assessmentFindings").value.trim(),
            recommended_action: document.getElementById("recommendedAction").value.trim(),
            assessment_outcome: document.getElementById("assessmentOutcome").value
        };

        if (payload.assessed_by.length < 2) {
            showMessage(
                "assessmentMessage",
                "Assessed By must contain at least 2 characters."
            );
            return;
        }

        if (payload.assessment_findings.length < 3) {
            showMessage(
                "assessmentMessage",
                "Technical Findings must contain at least 3 characters."
            );
            return;
        }

        if (payload.recommended_action.length < 3) {
            showMessage(
                "assessmentMessage",
                "Recommended Action must contain at least 3 characters."
            );
            return;
        }

        if (!payload.assessment_outcome) {
            showMessage(
                "assessmentMessage",
                "Please select an assessment outcome."
            );
            return;
        }

        submitAssessmentBtn.disabled = true;
        submitAssessmentBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Submitting...
        `;

        try {
            const response = await apiRequest("/team-assessments/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            showAssessmentResult(response);

            assessmentForm.reset();
            selectedAssignment = null;

            await loadPendingAssignments();

            assessmentFormSection.classList.add("d-none");
            complaintDetailsSection.classList.add("d-none");

        } catch (error) {
            showMessage("assessmentMessage", error.message);
        } finally {
            submitAssessmentBtn.disabled = false;
            submitAssessmentBtn.innerHTML = `
                <i class="bi bi-check-circle me-2"></i>Submit Assessment
            `;
        }
    });

    loadPendingAssignments();
});
