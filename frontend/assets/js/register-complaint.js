
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("registerComplaintForm");

    const serialNumberInput = document.getElementById("serialNumber");
    const verifyMachineBtn = document.getElementById("verifyMachineBtn");
    const registerComplaintBtn = document.getElementById("registerComplaintBtn");

    const machineDetailsSection = document.getElementById("machineDetailsSection");
    const machineVerificationMessage = document.getElementById("machineVerificationMessage");
    const registrationMessage = document.getElementById("registrationMessage");

    const verifiedSerialNumber = document.getElementById("verifiedSerialNumber");
    const modelNumber = document.getElementById("modelNumber");
    const batchNumber = document.getElementById("batchNumber");
    const manufacturingDate = document.getElementById("manufacturingDate");

    let verifiedMachine = null;

    function showMessage(element, message, type) {
        element.innerHTML = "";

        const alert = document.createElement("div");
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        element.appendChild(alert);
    }

    function getComplaintNumber(response) {
        const possibleLocations = [
            response?.complaint_number,
            response?.complaint?.complaint_number,
            response?.data?.complaint_number,
            response?.data?.complaint?.complaint_number,
            response?.result?.complaint_number,
            response?.result?.complaint?.complaint_number
        ];

        const complaintNumber = possibleLocations.find(
            value => typeof value === "string" && value.trim() !== ""
        );

        return complaintNumber || null;
    }

    function showRegistrationSuccess(response) {
        registrationMessage.innerHTML = "";

        const alert = document.createElement("div");
        alert.className = "alert alert-success";

        const heading = document.createElement("strong");
        heading.textContent = "Complaint Registered Successfully!";

        const message = document.createElement("p");
        message.className = "mb-2 mt-2";
        message.textContent =
            response?.message || "Your complaint has been registered successfully.";

        alert.appendChild(heading);
        alert.appendChild(message);

        const complaintNumber = getComplaintNumber(response);

        if (complaintNumber) {
            const numberLabel = document.createElement("div");
            numberLabel.className = "fw-semibold";
            numberLabel.textContent =
                `Generated Complaint Number: ${complaintNumber}`;

            alert.appendChild(numberLabel);

            const copyButton = document.createElement("button");
            copyButton.type = "button";
            copyButton.className = "btn btn-sm btn-outline-success mt-2";
            copyButton.innerHTML =
                '<i class="bi bi-copy me-1"></i>Copy Complaint Number';

            copyButton.addEventListener("click", async function () {
                try {
                    await navigator.clipboard.writeText(complaintNumber);
                    copyButton.innerHTML =
                        '<i class="bi bi-check-circle me-1"></i>Copied!';
                } catch (error) {
                    showMessage(
                        registrationMessage,
                        `Complaint Number: ${complaintNumber}. Please copy it manually.`,
                        "success"
                    );
                }
            });

            alert.appendChild(copyButton);
        }

        registrationMessage.appendChild(alert);
    }

    function clearMachineDetails() {
        verifiedMachine = null;

        machineDetailsSection.classList.add("d-none");

        verifiedSerialNumber.value = "";
        modelNumber.value = "";
        batchNumber.value = "";
        manufacturingDate.value = "";

        registerComplaintBtn.disabled = true;
    }

    function resetVerification() {
        clearMachineDetails();
        machineVerificationMessage.innerHTML = "";
        registrationMessage.innerHTML = "";
    }

    async function verifyMachine() {
        const serialNumber = serialNumberInput.value.trim();

        resetVerification();

        if (!serialNumber) {
            showMessage(
                machineVerificationMessage,
                "Please enter a machine serial number.",
                "warning"
            );
            serialNumberInput.focus();
            return;
        }

        verifyMachineBtn.disabled = true;
        verifyMachineBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2"></span>Verifying...';

        try {
            const response = await apiRequest(
                `/machines/${encodeURIComponent(serialNumber)}`
            );

            if (!response.machine) {
                throw new Error("Machine details were not returned by the server.");
            }

            verifiedMachine = response.machine;

            verifiedSerialNumber.value = verifiedMachine.serial_number || "";
            modelNumber.value = verifiedMachine.model_number || "";
            batchNumber.value = verifiedMachine.batch_number || "";
            manufacturingDate.value = formatDate(
                verifiedMachine.manufacturing_date
            );

            machineDetailsSection.classList.remove("d-none");

            showMessage(
                machineVerificationMessage,
                "Machine verified successfully.",
                "success"
            );

            registerComplaintBtn.disabled = false;

        } catch (error) {
            clearMachineDetails();

            showMessage(
                machineVerificationMessage,
                error.message || "Unable to verify the machine.",
                "danger"
            );

        } finally {
            verifyMachineBtn.disabled = false;
            verifyMachineBtn.innerHTML =
                '<i class="bi bi-search me-2"></i>Verify Machine';
        }
    }

    verifyMachineBtn.addEventListener("click", verifyMachine);

    serialNumberInput.addEventListener("input", function () {
        resetVerification();
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        if (!verifiedMachine) {
            showMessage(
                registrationMessage,
                "Please verify the machine before registering the complaint.",
                "warning"
            );
            return;
        }

        if (
            serialNumberInput.value.trim() !== verifiedMachine.serial_number
        ) {
            clearMachineDetails();

            showMessage(
                registrationMessage,
                "The machine serial number has changed. Please verify it again.",
                "warning"
            );
            return;
        }

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const complaintData = {
            serial_number: verifiedMachine.serial_number,
            customer_name: document.getElementById("customerName").value.trim(),
            customer_contact:
                document.getElementById("customerContact").value.trim() || null,
            dealer_email: document.getElementById("dealerEmail").value.trim(),
            reported_issue: document.getElementById("reportedIssue").value.trim(),
            registered_by: document.getElementById("registeredBy").value.trim()
        };

        registerComplaintBtn.disabled = true;
        registerComplaintBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2"></span>Registering...';

        try {
            const response = await apiRequest("/complaints/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(complaintData)
            });

            showRegistrationSuccess(response);

            form.reset();
            clearMachineDetails();
            machineVerificationMessage.innerHTML = "";

            // Bring the success message into the visible area.
            registrationMessage.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

        } catch (error) {
            showMessage(
                registrationMessage,
                error.message || "Unable to register the complaint.",
                "danger"
            );

            registrationMessage.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

        } finally {
            registerComplaintBtn.disabled = !verifiedMachine;
            registerComplaintBtn.innerHTML =
                '<i class="bi bi-check-circle me-2"></i>Register Complaint';
        }
    });

    form.addEventListener("reset", function () {
        window.setTimeout(function () {
            clearMachineDetails();
            machineVerificationMessage.innerHTML = "";
        }, 0);
    });
});
