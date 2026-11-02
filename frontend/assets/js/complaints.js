
const COMPLAINTS_PAGE_SIZE = 20;

let currentPage = 1;
let totalComplaints = 0;
let currentComplaints = [];
let searchTimer = null;
let complaintDetailsModal = null;

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

function formatLabel(value) {
    if (!value) return "-";

    return String(value)
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/\b\w/g, character => character.toUpperCase());
}

function getPriorityBadge(priority) {
    const value = (priority || "LOW").toLowerCase();

    return `<span class="priority-badge ${escapeHtml(value)}">
        ${escapeHtml(priority || "LOW")}
    </span>`;
}

function getStatusBadge(status) {
    const value = (status || "").toLowerCase();

    return `<span class="status-badge ${escapeHtml(value)}">
        ${escapeHtml(formatLabel(status))}
    </span>`;
}

function updateSummaryCards() {
    const totalElement = document.getElementById("totalComplaints");
    const repeatElement = document.getElementById("repeatComplaints");
    const recordsElement = document.getElementById("recordsOnPage");

    const repeatCount = currentComplaints.filter(
        complaint => complaint.is_repeat_complaint
    ).length;

    if (totalElement) {
        totalElement.textContent = totalComplaints;
    }

    if (repeatElement) {
        repeatElement.textContent = repeatCount;
    }

    if (recordsElement) {
        recordsElement.textContent = currentComplaints.length;
    }
}

function renderComplaintsTable() {
    const tableBody = document.getElementById("complaintsTableBody");

    if (!tableBody) return;

    if (currentComplaints.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center py-4">
                    No complaints found.
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = currentComplaints.map(complaint => `
        <tr>
            <td>
                <strong>${escapeHtml(complaint.complaint_number)}</strong>
            </td>
            <td>${escapeHtml(complaint.serial_number)}</td>
            <td>${escapeHtml(complaint.model_number)}</td>
            <td>${escapeHtml(complaint.customer_name)}</td>
            <td>${escapeHtml(complaint.reported_issue)}</td>
            <td>${escapeHtml(complaint.issue_type_name || "-")}</td>
            <td>${getPriorityBadge(complaint.priority)}</td>
            <td>${getStatusBadge(complaint.complaint_status)}</td>
            <td>${formatDate(complaint.registered_at)}</td>
            <td>
                <button
                    class="btn btn-sm btn-outline-primary"
                    onclick="viewComplaintDetails('${escapeHtml(complaint.complaint_number)}')">
                    <i class="bi bi-eye"></i> View
                </button>
            </td>
        </tr>
    `).join("");
}

function updatePagination() {
    const paginationInfo = document.getElementById("paginationInfo");
    const pageNumber = document.getElementById("pageNumber");
    const previousButton = document.getElementById("previousPageBtn");
    const nextButton = document.getElementById("nextPageBtn");

    const totalPages = Math.max(
        1,
        Math.ceil(totalComplaints / COMPLAINTS_PAGE_SIZE)
    );

    if (paginationInfo) {
        paginationInfo.textContent =
            `Showing ${currentComplaints.length} of ${totalComplaints} complaints`;
    }

    if (pageNumber) {
        pageNumber.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    if (previousButton) {
        previousButton.disabled = currentPage <= 1;
    }

    if (nextButton) {
        nextButton.disabled = currentPage >= totalPages;
    }
}

async function loadComplaints() {
    const search = document.getElementById("complaintSearch")?.value.trim() || "";
    const status = document.getElementById("statusFilter")?.value || "";
    const priority = document.getElementById("priorityFilter")?.value || "";

    const params = new URLSearchParams({
        limit: COMPLAINTS_PAGE_SIZE,
        offset: (currentPage - 1) * COMPLAINTS_PAGE_SIZE
    });

    if (search) params.append("search", search);
    if (status) params.append("complaint_status", status);
    if (priority) params.append("priority", priority);

    try {
        const response = await apiRequest(`/complaints/?${params.toString()}`);

        currentComplaints = response.data?.items || [];
        totalComplaints = response.data?.total || 0;

        renderComplaintsTable();
        updateSummaryCards();
        updatePagination();

    } catch (error) {
        console.error("Unable to load complaints:", error);

        showNotification(
            "Unable to load complaints. Please try again.",
            "error"
        );
    }
}

async function viewComplaintDetails(complaintNumber) {
    try {
        const response = await apiRequest(
            `/complaints/${encodeURIComponent(complaintNumber)}`
        );

        // The details endpoint returns the complaint under response.complaint.
        const complaint = response.complaint;

        if (!complaint) {
            throw new Error("Complaint details were not found.");
        }

        const title = document.getElementById("complaintDetailsTitle");
        const subtitle = document.getElementById("complaintDetailsSubtitle");
        const body = document.getElementById("complaintDetailsBody");

        if (!title || !subtitle || !body) {
            throw new Error("Complaint details modal elements were not found.");
        }

        title.textContent = complaint.complaint_number || "Complaint Details";

        subtitle.textContent =
            `${complaint.serial_number || "-"} | ${complaint.model_number || "-"}`;

        const fields = [
            ["Complaint Number", complaint.complaint_number],
            ["Machine Serial Number", complaint.serial_number],
            ["Model Number", complaint.model_number],
            ["Batch Number", complaint.batch_number],
            ["Customer Name", complaint.customer_name],
            ["Customer Contact", complaint.customer_contact],
            ["Dealer Email", complaint.dealer_email],
            ["Reported Issue", complaint.reported_issue],
            ["Category", complaint.category_name],
            ["Issue Type", complaint.issue_type_name],
            ["Priority", formatLabel(complaint.priority)],
            ["Complaint Status", formatLabel(complaint.complaint_status)],
            ["Repeat Complaint", complaint.is_repeat_complaint ? "Yes" : "No"],
            ["Previous Complaint", complaint.previous_complaint_number],
            ["Registered At", formatDate(complaint.registered_at)],
            ["Closed At", formatDate(complaint.closed_at)]
        ];

        body.innerHTML = `
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

        complaintDetailsModal.show();

    } catch (error) {
        console.error("Unable to retrieve complaint details:", error);

        showNotification(
            error.message || "Unable to retrieve complaint details.",
            "error"
        );
    }
}

function applyFilters() {
    currentPage = 1;
    loadComplaints();
}

function clearFilters() {
    document.getElementById("complaintSearch").value = "";
    document.getElementById("statusFilter").value = "";
    document.getElementById("priorityFilter").value = "";

    currentPage = 1;
    loadComplaints();
}

function goToPreviousPage() {
    if (currentPage > 1) {
        currentPage--;
        loadComplaints();
    }
}

function goToNextPage() {
    const totalPages = Math.ceil(totalComplaints / COMPLAINTS_PAGE_SIZE);

    if (currentPage < totalPages) {
        currentPage++;
        loadComplaints();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const modalElement = document.getElementById("complaintDetailsModal");

    if (modalElement) {
        complaintDetailsModal = new bootstrap.Modal(modalElement);
    }

    document.getElementById("applyFiltersBtn")
        ?.addEventListener("click", applyFilters);

    document.getElementById("clearFiltersBtn")
        ?.addEventListener("click", clearFilters);

    document.getElementById("refreshComplaintsBtn")
        ?.addEventListener("click", loadComplaints);

    document.getElementById("previousPageBtn")
        ?.addEventListener("click", goToPreviousPage);

    document.getElementById("nextPageBtn")
        ?.addEventListener("click", goToNextPage);

    document.getElementById("complaintSearch")
        ?.addEventListener("input", () => {
            clearTimeout(searchTimer);

            searchTimer = setTimeout(() => {
                currentPage = 1;
                loadComplaints();
            }, 400);
        });

    loadComplaints();
});
