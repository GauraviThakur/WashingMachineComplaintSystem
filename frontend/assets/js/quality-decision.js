
document.addEventListener("DOMContentLoaded", () => {
    const complaintNumberInput = document.getElementById("complaintNumber");
    const loadComplaintBtn = document.getElementById("loadComplaintBtn");

    const complaintDetailsSection = document.getElementById("complaintDetailsSection");
    const decisionFormSection = document.getElementById("decisionFormSection");
    const decisionResultSection = document.getElementById("decisionResultSection");
    const dispositionFormSection = document.getElementById("dispositionFormSection");
    const finalResultSection = document.getElementById("finalResultSection");
    const historySection = document.getElementById("historySection");

    const decisionForm = document.getElementById("decisionForm");
    const dispositionForm = document.getElementById("dispositionForm");

    const decisionTypeInput = document.getElementById("decisionType");
    const rejectionReasonSection = document.getElementById("rejectionReasonSection");
    const rejectionReasonInput = document.getElementById("rejectionReason");

    const submitDecisionBtn = document.getElementById("submitDecisionBtn");
    const submitDispositionBtn = document.getElementById("submitDispositionBtn");

    let currentComplaint = null;
    let currentHistory = null;

    const ACCEPTED_DISPOSITIONS = [
        {
            value: "RETURN_TO_STOCK",
            label: "Return to Stock"
        },
        {
            value: "RETURN_TO_DEALER",
            label: "Return to Dealer"
        }
    ];

    const REJECTED_DISPOSITIONS = [
        {
            value: "SCRAP",
            label: "Scrap"
        }
    ];

    const PHYSICAL_ACTIONS = {
        RETURN_TO_DEALER: {
            completionType: "DISPATCH",
            title: "Dealer Dispatch Completion",
            description: "Record the dispatch details after the machine has physically been dispatched to the dealer.",
            referenceLabel: "Dispatch Note Number",
            referenceRequired: true,
            referencePlaceholder: "Enter dispatch note number",
            buttonLabel: "Complete Dispatch"
        },

        RETURN_TO_STOCK: {
            completionType: "STOCK_TRANSFER",
            title: "Stock Transfer Completion",
            description: "Record the stock transfer details after the machine has physically been transferred to stock.",
            referenceLabel: "Stock Transfer Number",
            referenceRequired: true,
            referencePlaceholder: "Enter stock transfer number",
            buttonLabel: "Complete Stock Transfer"
        },

        SCRAP: {
            completionType: "SCRAP",
            title: "Scrap Completion",
            description: "Record the scrap activity after the machine has physically been scrapped.",
            referenceLabel: "Scrap Record Number",
            referenceRequired: false,
            referencePlaceholder: "Enter scrap record number (optional)",
            buttonLabel: "Complete Scrap"
        }
    };


    // --------------------------------------------------
    // COMMON HELPERS
    // --------------------------------------------------

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

        if (!container) {
            return;
        }

        container.innerHTML = `
            <div class="alert alert-${type} mb-0" role="alert">
                ${escapeHtml(message)}
            </div>
        `;
    }


    function clearMessage(containerId) {
        const container = document.getElementById(containerId);

        if (container) {
            container.innerHTML = "";
        }
    }


    function formatLabel(value) {
        if (!value) {
            return "-";
        }

        return String(value)
            .toLowerCase()
            .replaceAll("_", " ")
            .replace(/\b\w/g, character => character.toUpperCase());
    }


    function getComplaintObject(response) {
        return response?.complaint ||
            response?.data?.complaint ||
            response?.data ||
            response;
    }


    function getComplaintStatus(complaint) {
        return complaint?.complaint_status ||
            complaint?.status ||
            "";
    }


    function hideWorkflowSections() {
        complaintDetailsSection.classList.add("d-none");
        decisionFormSection.classList.add("d-none");
        decisionResultSection.classList.add("d-none");
        dispositionFormSection.classList.add("d-none");
        finalResultSection.classList.add("d-none");
        historySection.classList.add("d-none");
    }


    function clearWorkflowMessages() {
        clearMessage("pageMessage");
        clearMessage("decisionMessage");
        clearMessage("dispositionMessage");
    }


    // --------------------------------------------------
    // COMPLAINT INFORMATION
    // --------------------------------------------------

    function setComplaintDetails(complaint) {
        document.getElementById("detailComplaintNumber").value =
            complaint.complaint_number || "-";

        document.getElementById("detailSerialNumber").value =
            complaint.serial_number ||
            complaint.machine_serial_number ||
            "-";

        document.getElementById("detailModelNumber").value =
            complaint.model_number ||
            complaint.machine_model ||
            "-";

        document.getElementById("detailCustomerName").value =
            complaint.customer_name || "-";

        document.getElementById("detailDealerEmail").value =
            complaint.dealer_email || "-";

        document.getElementById("detailComplaintStatus").value =
            formatLabel(getComplaintStatus(complaint));

        document.getElementById("detailReportedIssue").value =
            complaint.reported_issue || "-";
    }


    // --------------------------------------------------
    // QUALITY DECISION
    // --------------------------------------------------

    function canRecordDecision(complaint) {
        const status = getComplaintStatus(complaint);

        return (
            status === "AWAITING_DECISION" ||
            status === "AWAITING_QUALITY_REVIEW"
        );
    }


    function updateRejectionReasonVisibility() {
        const isRejected = decisionTypeInput.value === "REJECTED";

        rejectionReasonSection.classList.toggle("d-none", !isRejected);
        rejectionReasonInput.required = isRejected;

        if (!isRejected) {
            rejectionReasonInput.value = "";
        }
    }


    function showDecisionResult(response) {
        const result = response?.data || response;

        const decision = result?.decision || {};
        const decisionType =
            decision.decision_type ||
            result.decision_type ||
            decisionTypeInput.value;

        const complaintStatus =
            result?.complaint_status ||
            result?.current_status ||
            "-";

        document.getElementById("decisionResultBody").innerHTML = `
            <div class="alert alert-success mb-0">
                <h6>
                    <i class="bi bi-check-circle me-2"></i>
                    Quality decision recorded successfully
                </h6>

                <p class="mb-1">
                    <strong>Decision:</strong>
                    ${escapeHtml(formatLabel(decisionType))}
                </p>

                <p class="mb-1">
                    <strong>Complaint Status:</strong>
                    ${escapeHtml(formatLabel(complaintStatus))}
                </p>

                <p class="mb-0">
                    The complaint can now proceed to Final Disposition.
                </p>
            </div>
        `;

        decisionResultSection.classList.remove("d-none");
    }


    // --------------------------------------------------
    // FINAL DISPOSITION
    // --------------------------------------------------

    function populateDispositionOptions(decisionType) {
        const dispositionSelect = document.getElementById("dispositionType");

        const options = decisionType === "REJECTED"
            ? REJECTED_DISPOSITIONS
            : ACCEPTED_DISPOSITIONS;

        dispositionSelect.innerHTML = `
            <option value="">Select disposition</option>
            ${options.map(option => `
                <option value="${escapeHtml(option.value)}">
                    ${escapeHtml(option.label)}
                </option>
            `).join("")}
        `;

        document.getElementById("recordedDecisionType").value =
            formatLabel(decisionType);

        const information = document.getElementById("dispositionInfo");

        if (decisionType === "REJECTED") {
            information.innerHTML = `
                <i class="bi bi-info-circle me-2"></i>
                This machine was rejected. Its permitted disposition is
                <strong>SCRAP</strong>.
            `;
        } else {
            information.innerHTML = `
                <i class="bi bi-info-circle me-2"></i>
                This machine was accepted. Choose either
                <strong>RETURN TO STOCK</strong> or
                <strong>RETURN TO DEALER</strong>.
            `;
        }
    }


    function canRecordDisposition(complaint, history) {
        return (
            getComplaintStatus(complaint) === "AWAITING_DISPOSITION" &&
            Boolean(history?.decision) &&
            !history?.disposition
        );
    }


    function getPhysicalAction(dispositionType) {
        return PHYSICAL_ACTIONS[dispositionType] || null;
    }


    // --------------------------------------------------
    // PHYSICAL COMPLETION FORM
    // --------------------------------------------------

    function showPhysicalCompletionForm(disposition) {
        const action = getPhysicalAction(disposition?.disposition_type);

        if (!action) {
            showFinalResultMessage(
                "The disposition was recorded, but its physical action could not be identified.",
                "warning"
            );
            return;
        }

        document.getElementById("finalResultBody").innerHTML = `
            <div class="alert alert-warning">
                <h6 class="mb-1">
                    <i class="bi bi-hourglass-split me-2"></i>
                    Physical Action Pending
                </h6>

                <p class="mb-0">
                    The disposition has been recorded. The complaint
                    will remain open until the physical action is completed.
                </p>
            </div>

            <div class="border rounded p-3">
                <h6 class="mb-3">
                    <i class="bi bi-box-seam me-2"></i>
                    ${escapeHtml(action.title)}
                </h6>

                <p class="text-muted">
                    ${escapeHtml(action.description)}
                </p>

                <form id="physicalCompletionForm">

                    <div class="row g-3">

                        <div class="col-md-6">
                            <label class="form-label">
                                Complaint Number
                            </label>

                            <input
                                type="text"
                                class="form-control"
                                value="${escapeHtml(currentComplaint.complaint_number)}"
                                readonly
                            >
                        </div>

                        <div class="col-md-6">
                            <label class="form-label">
                                Completion Type
                            </label>

                            <input
                                type="text"
                                class="form-control"
                                value="${escapeHtml(formatLabel(action.completionType))}"
                                readonly
                            >
                        </div>

                        <div class="col-12">
                            <label for="completionReferenceNumber" class="form-label">
                                ${escapeHtml(action.referenceLabel)}
                                ${action.referenceRequired
                                    ? '<span class="text-danger">*</span>'
                                    : ''}
                            </label>

                            <input
                                type="text"
                                class="form-control"
                                id="completionReferenceNumber"
                                maxlength="100"
                                ${action.referenceRequired ? "required" : ""}
                                placeholder="${escapeHtml(action.referencePlaceholder)}"
                            >
                        </div>

                        <div class="col-12">
                            <label for="completionDetails" class="form-label">
                                Completion Details
                            </label>

                            <textarea
                                class="form-control"
                                id="completionDetails"
                                rows="3"
                                maxlength="5000"
                                placeholder="Enter any additional completion details (optional)..."
                            ></textarea>
                        </div>

                        <div class="col-md-6">
                            <label for="completedBy" class="form-label">
                                Completed By
                                <span class="text-danger">*</span>
                            </label>

                            <input
                                type="text"
                                class="form-control"
                                id="completedBy"
                                minlength="2"
                                maxlength="150"
                                required
                                placeholder="Enter responsible person's name"
                            >
                        </div>

                    </div>

                    <div id="physicalCompletionMessage" class="mt-3"></div>

                    <div class="d-flex justify-content-end mt-3">
                        <button
                            type="submit"
                            class="btn btn-primary"
                            id="submitPhysicalCompletionBtn"
                        >
                            <i class="bi bi-check-circle me-2"></i>
                            ${escapeHtml(action.buttonLabel)}
                        </button>
                    </div>

                </form>
            </div>
        `;

        finalResultSection.classList.remove("d-none");

        document
            .getElementById("physicalCompletionForm")
            .addEventListener("submit", submitPhysicalCompletion);
    }


    function showFinalResultMessage(message, type = "success") {
        document.getElementById("finalResultBody").innerHTML = `
            <div class="alert alert-${escapeHtml(type)} mb-0">
                ${escapeHtml(message)}
            </div>
        `;

        finalResultSection.classList.remove("d-none");
    }


    function showCompletionSuccess(response) {
        const result = response?.data || response;
        const completion = result?.physical_completion || {};

        const completionType =
            completion.completion_type || "";

        const referenceNumber =
            completion.reference_number || "Not provided";

        const completedBy =
            completion.completed_by || "-";

        const completedAt =
            completion.completed_at || "-";

        document.getElementById("finalResultBody").innerHTML = `
            <div class="alert alert-success mb-0">
                <h6>
                    <i class="bi bi-check-circle-fill me-2"></i>
                    Physical Action Completed Successfully
                </h6>

                <p class="mb-1">
                    <strong>Completion Type:</strong>
                    ${escapeHtml(formatLabel(completionType))}
                </p>

                <p class="mb-1">
                    <strong>Reference Number:</strong>
                    ${escapeHtml(referenceNumber)}
                </p>

                <p class="mb-1">
                    <strong>Completed By:</strong>
                    ${escapeHtml(completedBy)}
                </p>

                <p class="mb-1">
                    <strong>Completed At:</strong>
                    ${escapeHtml(completedAt)}
                </p>

                <p class="mb-0">
                    <strong>Complaint Status:</strong>
                    ${escapeHtml(formatLabel(result?.complaint_status || "CLOSED"))}
                </p>

                <hr>

                <p class="mb-0">
                    The physical action has been recorded and the complaint
                    has been closed successfully.
                </p>
            </div>
        `;

        finalResultSection.classList.remove("d-none");
    }


    async function submitPhysicalCompletion(event) {
        event.preventDefault();

        const form = event.currentTarget;

        const submitButton = document.getElementById(
            "submitPhysicalCompletionBtn"
        );

        clearMessage("physicalCompletionMessage");

        if (!currentComplaint || !currentHistory?.disposition) {
            showMessage(
                "physicalCompletionMessage",
                "A recorded disposition is required before physical completion."
            );
            return;
        }

        const action = getPhysicalAction(
            currentHistory.disposition.disposition_type
        );

        if (!action) {
            showMessage(
                "physicalCompletionMessage",
                "The physical action could not be identified."
            );
            return;
        }

        const payload = {
            complaint_number: currentComplaint.complaint_number,
            completion_type: action.completionType,
            reference_number:
                document.getElementById("completionReferenceNumber").value.trim() || null,
            completion_details:
                document.getElementById("completionDetails").value.trim() || null,
            completed_by:
                document.getElementById("completedBy").value.trim()
        };

        if (
            action.referenceRequired &&
            !payload.reference_number
        ) {
            showMessage(
                "physicalCompletionMessage",
                "A reference number is required for this physical action."
            );
            return;
        }

        if (payload.completed_by.length < 2) {
            showMessage(
                "physicalCompletionMessage",
                "Please enter the responsible person's name."
            );
            return;
        }

        submitButton.disabled = true;
        submitButton.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Saving Completion...
        `;

        try {
            const response = await apiRequest(
                "/decision-disposition/physical-completion",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                }
            );

            showCompletionSuccess(response);

            const refreshedResponse = await apiRequest(
                `/complaints/${encodeURIComponent(currentComplaint.complaint_number)}`
            );

            currentComplaint = getComplaintObject(refreshedResponse);

            setComplaintDetails(currentComplaint);

            await loadDecisionDispositionHistory(
                currentComplaint.complaint_number
            );

            updateWorkflowSections();

        } catch (error) {
            showMessage(
                "physicalCompletionMessage",
                error.message
            );

            submitButton.disabled = false;
            submitButton.innerHTML = `
                <i class="bi bi-check-circle me-2"></i>
                ${escapeHtml(action.buttonLabel)}
            `;
        }
    }


    // --------------------------------------------------
    // DECISION AND DISPOSITION HISTORY
    // --------------------------------------------------

    function renderHistory(history) {
        const historyBody = document.getElementById("historyBody");

        const decision = history?.decision;
        const disposition = history?.disposition;
        const completion = history?.physical_completion;

        let html = `
            <div class="mb-3">
                <strong>Current Complaint Status:</strong>
                <span class="badge bg-primary ms-1">
                    ${escapeHtml(formatLabel(history?.complaint_status))}
                </span>
            </div>
        `;

        if (decision) {
            html += `
                <div class="border rounded p-3 mb-3">
                    <h6 class="mb-3">
                        <i class="bi bi-patch-check me-2"></i>
                        Quality Decision
                    </h6>

                    <div class="row g-3">

                        <div class="col-md-6">
                            <strong>Decision:</strong>
                            ${escapeHtml(formatLabel(decision.decision_type))}
                        </div>

                        <div class="col-md-6">
                            <strong>Decided By:</strong>
                            ${escapeHtml(decision.decided_by || "-")}
                        </div>

                        <div class="col-12">
                            <strong>Decision Reason:</strong>
                            <p class="mb-0">
                                ${escapeHtml(decision.decision_reason || "-")}
                            </p>
                        </div>

                        ${decision.rejection_reason ? `
                            <div class="col-12">
                                <strong>Rejection Reason:</strong>
                                <p class="mb-0">
                                    ${escapeHtml(decision.rejection_reason)}
                                </p>
                            </div>
                        ` : ""}

                        <div class="col-12">
                            <strong>Decision Date:</strong>
                            ${escapeHtml(decision.decided_at || "-")}
                        </div>

                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="alert alert-secondary">
                    No quality decision has been recorded yet.
                </div>
            `;
        }

        if (disposition) {
            html += `
                <div class="border rounded p-3 mb-3">
                    <h6 class="mb-3">
                        <i class="bi bi-box-seam me-2"></i>
                        Final Disposition
                    </h6>

                    <div class="row g-3">

                        <div class="col-md-6">
                            <strong>Disposition:</strong>
                            ${escapeHtml(formatLabel(disposition.disposition_type))}
                        </div>

                        <div class="col-md-6">
                            <strong>Recorded By:</strong>
                            ${escapeHtml(disposition.recorded_by || "-")}
                        </div>

                        <div class="col-12">
                            <strong>Disposition Reason:</strong>
                            <p class="mb-0">
                                ${escapeHtml(disposition.disposition_reason || "-")}
                            </p>
                        </div>

                        <div class="col-12">
                            <strong>Recorded Date:</strong>
                            ${escapeHtml(disposition.recorded_at || "-")}
                        </div>

                    </div>
                </div>
            `;
        } else if (decision) {
            html += `
                <div class="alert alert-warning">
                    A quality decision has been recorded, but the final
                    disposition has not yet been recorded.
                </div>
            `;
        }

        if (completion) {
            html += `
                <div class="border rounded p-3">
                    <h6 class="mb-3">
                        <i class="bi bi-check-circle me-2"></i>
                        Physical Completion
                    </h6>

                    <div class="row g-3">

                        <div class="col-md-6">
                            <strong>Completion Type:</strong>
                            ${escapeHtml(formatLabel(completion.completion_type))}
                        </div>

                        <div class="col-md-6">
                            <strong>Reference Number:</strong>
                            ${escapeHtml(completion.reference_number || "Not provided")}
                        </div>

                        <div class="col-md-6">
                            <strong>Completed By:</strong>
                            ${escapeHtml(completion.completed_by || "-")}
                        </div>

                        <div class="col-md-6">
                            <strong>Completed At:</strong>
                            ${escapeHtml(completion.completed_at || "-")}
                        </div>

                        <div class="col-12">
                            <strong>Completion Details:</strong>
                            <p class="mb-0">
                                ${escapeHtml(completion.completion_details || "-")}
                            </p>
                        </div>

                    </div>
                </div>
            `;
        } else if (disposition) {
            html += `
                <div class="alert alert-warning mb-0">
                    Physical completion is pending. The complaint
                    cannot be closed until the action is recorded.
                </div>
            `;
        }

        historyBody.innerHTML = html;
        historySection.classList.remove("d-none");
    }


    async function loadDecisionDispositionHistory(complaintNumber) {
        try {
            const response = await apiRequest(
                `/decision-disposition/${encodeURIComponent(complaintNumber)}`
            );

            currentHistory = response?.data || response;

            renderHistory(currentHistory);

            return currentHistory;

        } catch (error) {
            currentHistory = null;

            document.getElementById("historyBody").innerHTML = `
                <div class="alert alert-warning mb-0">
                    Unable to load decision and disposition history:
                    ${escapeHtml(error.message)}
                </div>
            `;

            historySection.classList.remove("d-none");

            throw error;
        }
    }


    // --------------------------------------------------
    // WORKFLOW DISPLAY
    // --------------------------------------------------

    function updateWorkflowSections() {
        if (!currentComplaint) {
            return;
        }

        const status = getComplaintStatus(currentComplaint);
        const decision = currentHistory?.decision;
        const disposition = currentHistory?.disposition;
        const completion = currentHistory?.physical_completion;

        decisionFormSection.classList.add("d-none");
        dispositionFormSection.classList.add("d-none");

        if (!decision && canRecordDecision(currentComplaint)) {
            decisionFormSection.classList.remove("d-none");
            return;
        }

        if (
            decision &&
            !disposition &&
            canRecordDisposition(currentComplaint, currentHistory)
        ) {
            populateDispositionOptions(decision.decision_type);
            dispositionFormSection.classList.remove("d-none");
            return;
        }

        if (disposition && !completion) {
            showPhysicalCompletionForm(disposition);
            return;
        }

        if (status === "CLOSED" && completion) {
            return;
        }

        if (!decision && !canRecordDecision(currentComplaint)) {
            showMessage(
                "pageMessage",
                `A quality decision cannot be recorded because the complaint status is ${formatLabel(status)}. A decision is allowed only for AWAITING_DECISION or AWAITING_QUALITY_REVIEW complaints.`,
                "warning"
            );
            return;
        }

        if (decision && !disposition && status !== "AWAITING_DISPOSITION") {
            showMessage(
                "pageMessage",
                `A final disposition cannot be recorded because the complaint status is ${formatLabel(status)}.`,
                "warning"
            );
        }
    }


    // --------------------------------------------------
    // LOAD COMPLAINT
    // --------------------------------------------------

    async function loadComplaint() {
        const complaintNumber = complaintNumberInput.value.trim();

        clearWorkflowMessages();
        hideWorkflowSections();

        currentComplaint = null;
        currentHistory = null;

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

            await loadDecisionDispositionHistory(
                complaint.complaint_number
            );

            updateWorkflowSections();

        } catch (error) {
            showMessage("pageMessage", error.message);
        } finally {
            loadComplaintBtn.disabled = false;
            loadComplaintBtn.innerHTML = `
                <i class="bi bi-search me-2"></i>Load Complaint
            `;
        }
    }


    // --------------------------------------------------
    // SUBMIT QUALITY DECISION
    // --------------------------------------------------

    decisionForm.addEventListener("submit", async event => {
        event.preventDefault();

        clearMessage("decisionMessage");

        if (!currentComplaint) {
            showMessage(
                "decisionMessage",
                "Load a complaint before recording a quality decision."
            );
            return;
        }

        if (!canRecordDecision(currentComplaint)) {
            showMessage(
                "decisionMessage",
                "This complaint is not currently eligible for a quality decision."
            );
            return;
        }

        const payload = {
            complaint_number: currentComplaint.complaint_number,
            decision_type: decisionTypeInput.value,
            decision_reason: document.getElementById("decisionReason").value.trim(),
            rejection_reason: rejectionReasonInput.value.trim() || null,
            decided_by: document.getElementById("decidedBy").value.trim()
        };

        if (
            !payload.decision_type ||
            payload.decision_reason.length < 3 ||
            payload.decided_by.length < 2
        ) {
            showMessage(
                "decisionMessage",
                "Please complete all required decision fields correctly."
            );
            return;
        }

        if (
            payload.decision_type === "REJECTED" &&
            (!payload.rejection_reason || payload.rejection_reason.length < 3)
        ) {
            showMessage(
                "decisionMessage",
                "A rejection reason of at least 3 characters is mandatory."
            );
            return;
        }

        submitDecisionBtn.disabled = true;
        submitDecisionBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Submitting...
        `;

        try {
            const response = await apiRequest("/decision-disposition/decision", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            showDecisionResult(response);

            decisionForm.reset();
            updateRejectionReasonVisibility();

            showMessage(
                "decisionMessage",
                "Quality decision saved successfully.",
                "success"
            );

            const refreshedResponse = await apiRequest(
                `/complaints/${encodeURIComponent(currentComplaint.complaint_number)}`
            );

            currentComplaint = getComplaintObject(refreshedResponse);

            setComplaintDetails(currentComplaint);

            await loadDecisionDispositionHistory(
                currentComplaint.complaint_number
            );

            updateWorkflowSections();

        } catch (error) {
            showMessage("decisionMessage", error.message);
        } finally {
            submitDecisionBtn.disabled = false;
            submitDecisionBtn.innerHTML = `
                <i class="bi bi-check-circle me-2"></i>Submit Decision
            `;
        }
    });


    // --------------------------------------------------
    // SUBMIT FINAL DISPOSITION
    // --------------------------------------------------

    dispositionForm.addEventListener("submit", async event => {
        event.preventDefault();

        clearMessage("dispositionMessage");

        if (!currentComplaint || !currentHistory?.decision) {
            showMessage(
                "dispositionMessage",
                "A recorded quality decision is required before submitting disposition."
            );
            return;
        }

        if (!canRecordDisposition(currentComplaint, currentHistory)) {
            showMessage(
                "dispositionMessage",
                "This complaint is not currently eligible for final disposition."
            );
            return;
        }

        const payload = {
            complaint_number: currentComplaint.complaint_number,
            disposition_type: document.getElementById("dispositionType").value,
            disposition_reason: document.getElementById("dispositionReason").value.trim(),
            recorded_by: document.getElementById("recordedBy").value.trim()
        };

        if (
            !payload.disposition_type ||
            payload.disposition_reason.length < 3 ||
            payload.recorded_by.length < 2
        ) {
            showMessage(
                "dispositionMessage",
                "Please complete all required disposition fields correctly."
            );
            return;
        }

        submitDispositionBtn.disabled = true;
        submitDispositionBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Submitting...
        `;

        try {
            await apiRequest(
                "/decision-disposition/disposition",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                }
            );

            dispositionForm.reset();

            showMessage(
                "dispositionMessage",
                "Final disposition saved successfully. Physical completion is now required.",
                "success"
            );

            const refreshedResponse = await apiRequest(
                `/complaints/${encodeURIComponent(currentComplaint.complaint_number)}`
            );

            currentComplaint = getComplaintObject(refreshedResponse);

            setComplaintDetails(currentComplaint);

            await loadDecisionDispositionHistory(
                currentComplaint.complaint_number
            );

            updateWorkflowSections();

        } catch (error) {
            showMessage("dispositionMessage", error.message);
        } finally {
            submitDispositionBtn.disabled = false;
            submitDispositionBtn.innerHTML = `
                <i class="bi bi-check-circle me-2"></i>Submit Disposition
            `;
        }
    });


    // --------------------------------------------------
    // EVENT LISTENERS
    // --------------------------------------------------

    loadComplaintBtn.addEventListener("click", loadComplaint);

    complaintNumberInput.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            loadComplaint();
        }
    });

    decisionTypeInput.addEventListener(
        "change",
        updateRejectionReasonVisibility
    );

    decisionForm.addEventListener("reset", () => {
        setTimeout(() => {
            clearMessage("decisionMessage");
            updateRejectionReasonVisibility();
        }, 0);
    });

    dispositionForm.addEventListener("reset", () => {
        setTimeout(() => {
            clearMessage("dispositionMessage");
        }, 0);
    });

});
