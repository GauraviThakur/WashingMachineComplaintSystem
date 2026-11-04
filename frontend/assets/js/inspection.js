
document.addEventListener("DOMContentLoaded", function () {

    /* =========================================
       HTML ESCAPING
    ========================================= */

    function escapeHtml(value) {
        if (value === null || value === undefined) {
            return "-";
        }

        return String(value).replace(/[&<>"']/g, character => {
            const entities = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            };

            return entities[character];
        });
    }


    const complaintNumberInput = document.getElementById("complaintNumber");
    const loadComplaintBtn = document.getElementById("loadComplaintBtn");

    const complaintDetailsSection = document.getElementById("complaintDetailsSection");
    const inspectionFormSection = document.getElementById("inspectionFormSection");
    const inspectionResultSection = document.getElementById("inspectionResultSection");

    const inspectionForm = document.getElementById("inspectionForm");

    const issueTypeSelect = document.getElementById("issueTypeId");
    const inspectionOutcomeSelect = document.getElementById("inspectionOutcome");

    const submitInspectionBtn = document.getElementById("submitInspectionBtn");

    const pageMessage = document.getElementById("pageMessage");
    const inspectionMessage = document.getElementById("inspectionMessage");

    let currentComplaint = null;
    let issueTypesLoaded = false;


    /* =========================================
       MESSAGE HANDLING
    ========================================= */

    function showMessage(element, message, type) {

        element.innerHTML = "";

        const alert = document.createElement("div");
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        element.appendChild(alert);
    }


    /* =========================================
       RESET DISPLAY
    ========================================= */

    function clearComplaintDisplay() {

        currentComplaint = null;

        complaintDetailsSection.classList.add("d-none");
        inspectionFormSection.classList.add("d-none");
        inspectionResultSection.classList.add("d-none");

        inspectionForm.reset();

        inspectionMessage.innerHTML = "";
        document.getElementById("inspectionResultBody").innerHTML = "";
    }


    /* =========================================
       LOAD ISSUE TYPES
    ========================================= */

    async function loadIssueTypes() {

        if (issueTypesLoaded) {
            return;
        }

        issueTypeSelect.innerHTML =
            '<option value="">Select issue type</option>';

        try {

            const response = await apiRequest("/issue-types/");

            const issueTypes = response.issue_types || [];

            issueTypes.forEach(issueType => {

                const option = document.createElement("option");

                option.value = issueType.issue_type_id;
                option.textContent = issueType.issue_type_name;

                issueTypeSelect.appendChild(option);

            });

            issueTypesLoaded = true;

        } catch (error) {

            console.error("Unable to load issue types:", error);

            throw new Error(
                "Unable to load issue types. Please refresh the page and try again."
            );
        }
    }


    /* =========================================
       DISPLAY COMPLAINT DETAILS
    ========================================= */

    function displayComplaintDetails(complaint) {

        document.getElementById("detailComplaintNumber").value =
            complaint.complaint_number || "";

        document.getElementById("detailSerialNumber").value =
            complaint.serial_number || "";

        document.getElementById("detailModelNumber").value =
            complaint.model_number || "";

        document.getElementById("detailCustomerName").value =
            complaint.customer_name || "";

        document.getElementById("detailDealerEmail").value =
            complaint.dealer_email || "";

        document.getElementById("detailComplaintStatus").value =
            (complaint.complaint_status || "").replaceAll("_", " ");

        document.getElementById("detailReportedIssue").value =
            complaint.reported_issue || "";

        complaintDetailsSection.classList.remove("d-none");
    }


    /* =========================================
       LOAD COMPLAINT
    ========================================= */

    async function loadComplaint() {

        const complaintNumber = complaintNumberInput.value.trim();

        pageMessage.innerHTML = "";
        clearComplaintDisplay();

        if (!complaintNumber) {

            showMessage(
                pageMessage,
                "Please enter a complaint number.",
                "warning"
            );

            complaintNumberInput.focus();
            return;
        }

        loadComplaintBtn.disabled = true;

        loadComplaintBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';

        try {

            const response = await apiRequest(
                `/complaints/${encodeURIComponent(complaintNumber)}`
            );

            const complaint = response.complaint;

            if (!complaint) {
                throw new Error("Complaint details were not returned by the server.");
            }

            currentComplaint = complaint;

            const allowedStatuses = [
                "REGISTERED",
                "UNDER_INSPECTION"
            ];

            if (!allowedStatuses.includes(complaint.complaint_status)) {

                displayComplaintDetails(complaint);

                showMessage(
                    pageMessage,
                    `This complaint cannot be inspected in its current status: ${complaint.complaint_status}.`,
                    "warning"
                );

                return;
            }

            await loadIssueTypes();

            displayComplaintDetails(complaint);

            inspectionFormSection.classList.remove("d-none");

            showMessage(
                pageMessage,
                "Complaint loaded successfully. You can now record the inspection.",
                "success"
            );

        } catch (error) {

            currentComplaint = null;

            showMessage(
                pageMessage,
                error.message || "Unable to load complaint details.",
                "danger"
            );

        } finally {

            loadComplaintBtn.disabled = false;

            loadComplaintBtn.innerHTML =
                '<i class="bi bi-search me-2"></i>Load Complaint';
        }
    }


    /* =========================================
       VALIDATE INSPECTION OUTCOME
    ========================================= */

    function validateInspectionSelection() {

        const outcome = inspectionOutcomeSelect.value;
        const issueTypeId = issueTypeSelect.value;

        const outcomesRequiringIssueType = [
            "ISSUE_IDENTIFIED",
            "REPAIR_REQUIRED"
        ];

        if (
            outcomesRequiringIssueType.includes(outcome) &&
            !issueTypeId
        ) {

            showMessage(
                inspectionMessage,
                "Please select an issue type for this inspection outcome.",
                "warning"
            );

            issueTypeSelect.focus();
            return false;
        }

        return true;
    }


    /* =========================================
       DISPLAY INSPECTION RESULT
    ========================================= */

    function displayInspectionResult(response) {

        const resultBody = document.getElementById("inspectionResultBody");

        const result = response.data || response;

        const complaintNumber =
            result.complaint_number ||
            currentComplaint?.complaint_number ||
            "-";

        const status =
            result.current_status ||
            result.complaint_status ||
            "-";

        const fields = [
            ["Complaint Number", complaintNumber],
            ["Previous Status", result.previous_status || "-"],
            ["Current Status", status]
        ];

        resultBody.innerHTML = `
            <div class="alert alert-success">
                ${escapeHtml(response.message || "Inspection recorded successfully.")}
            </div>

            <div class="row g-3">
                ${fields.map(([label, value]) => `
                    <div class="col-md-6">
                        <div class="border rounded p-3 h-100">
                            <small class="text-muted d-block mb-1">
                                ${escapeHtml(label)}
                            </small>
                            <strong>${escapeHtml(value)}</strong>
                        </div>
                    </div>
                `).join("")}
            </div>
        `;

        inspectionResultSection.classList.remove("d-none");
    }


    /* =========================================
       SUBMIT INSPECTION
    ========================================= */

    inspectionForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        inspectionMessage.innerHTML = "";

        if (!currentComplaint) {

            showMessage(
                inspectionMessage,
                "Please load a complaint before recording an inspection.",
                "warning"
            );

            return;
        }

        if (!inspectionForm.checkValidity()) {
            inspectionForm.reportValidity();
            return;
        }

        if (!validateInspectionSelection()) {
            return;
        }

        const inspectionData = {

            complaint_number: currentComplaint.complaint_number,

            inspected_by:
                document.getElementById("inspectedBy").value.trim(),

            inspection_findings:
                document.getElementById("inspectionFindings").value.trim(),

            issue_type_id: issueTypeSelect.value
                ? Number(issueTypeSelect.value)
                : null,

            inspection_outcome: inspectionOutcomeSelect.value,

            recommended_action:
                document.getElementById("recommendedAction").value.trim() || null,

            inspection_notes:
                document.getElementById("inspectionNotes").value.trim() || null
        };

        submitInspectionBtn.disabled = true;

        submitInspectionBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';

        try {

            const response = await apiRequest("/inspections/", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(inspectionData)
            });

            displayInspectionResult(response);

            inspectionFormSection.classList.add("d-none");

            showMessage(
                pageMessage,
                "Inspection has been recorded successfully.",
                "success"
            );

            inspectionResultSection.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

            currentComplaint = null;

        } catch (error) {

            showMessage(
                inspectionMessage,
                error.message || "Unable to submit inspection.",
                "danger"
            );

        } finally {

            submitInspectionBtn.disabled = false;

            submitInspectionBtn.innerHTML =
                '<i class="bi bi-check-circle me-2"></i>Submit Inspection';
        }
    });


    /* =========================================
       EVENT LISTENERS
    ========================================= */

    loadComplaintBtn.addEventListener("click", loadComplaint);

    complaintNumberInput.addEventListener("input", function () {

        pageMessage.innerHTML = "";

        clearComplaintDisplay();
    });

    inspectionOutcomeSelect.addEventListener("change", function () {

        const outcome = inspectionOutcomeSelect.value;

        if (
            outcome === "NO_ISSUE_FOUND" ||
            outcome === "FURTHER_TESTING_REQUIRED"
        ) {
            issueTypeSelect.value = "";
        }
    });

    inspectionForm.addEventListener("reset", function () {

        window.setTimeout(function () {
            inspectionMessage.innerHTML = "";
        }, 0);
    });

});
