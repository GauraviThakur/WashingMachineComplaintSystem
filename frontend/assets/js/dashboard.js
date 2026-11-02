
/* =========================================
   1. CHART INSTANCES
========================================= */

let statusChartInstance = null;
let priorityChartInstance = null;
let teamWorkloadChartInstance = null;
let decisionChartInstance = null;


/* =========================================
   2. INITIALIZE DASHBOARD
========================================= */

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();

    const refreshButton = document.getElementById(
        "refreshDashboardBtn"
    );

    if (refreshButton) {
        refreshButton.addEventListener("click", loadDashboard);
    }
});


/* =========================================
   3. LOAD COMPLETE DASHBOARD
========================================= */

async function loadDashboard() {
    const refreshButton = document.getElementById(
        "refreshDashboardBtn"
    );

    setRefreshButtonLoading(true);

    const dashboardTasks = [
        loadDashboardSummary(),
        loadStatusChart(),
        loadPriorityChart(),
        loadTeamWorkloadChart(),
        loadDecisionChart(),
        loadRecentComplaints()
    ];

    const results = await Promise.allSettled(dashboardTasks);

    const failedTasks = results.filter(
        result => result.status === "rejected"
    );

    if (failedTasks.length > 0) {
        console.error("Some dashboard sections could not load:", failedTasks);

        showNotification(
            "Some dashboard information could not be loaded. Please check the failed sections.",
            "error"
        );
    }

    setRefreshButtonLoading(false);
}


/* =========================================
   4. API RESPONSE HELPER
========================================= */

function extractData(response) {
    return response?.data ?? response;
}


/* =========================================
   5. SUMMARY CARDS
========================================= */

async function loadDashboardSummary() {
    try {
        const response = await apiRequest("/dashboard/summary");
        const data = extractData(response);

        setElementText("totalComplaints", data.total_complaints);
        setElementText("openComplaints", data.open_complaints);
        setElementText("closedComplaints", data.closed_complaints);
        setElementText("repeatComplaints", data.repeat_complaints);

    } catch (error) {
        console.error("Dashboard summary error:", error);

        setSummaryCardsError();
        throw error;
    }
}


function setSummaryCardsError() {
    const cardIds = [
        "totalComplaints",
        "openComplaints",
        "closedComplaints",
        "repeatComplaints"
    ];

    cardIds.forEach(id => {
        setElementText(id, "--");
    });
}


/* =========================================
   6. COMPLAINT STATUS CHART
========================================= */

async function loadStatusChart() {
    try {
        const response = await apiRequest(
            "/dashboard/status-counts"
        );

        const data = extractData(response) || [];

        const labels = data.map(item =>
            formatLabel(item.status)
        );

        const values = data.map(item =>
            Number(item.count) || 0
        );

        const canvas = document.getElementById("statusChart");

        if (!canvas) return;

        if (statusChartInstance) {
            statusChartInstance.data.labels = labels;
            statusChartInstance.data.datasets[0].data = values;
            statusChartInstance.update();
            return;
        }

        statusChartInstance = new Chart(canvas, {
            type: "bar",

            data: {
                labels: labels,

                datasets: [{
                    label: "Complaints",
                    data: values,
                    backgroundColor: "#168b9c",
                    borderRadius: 6,
                    barThickness: 35
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display: false
                    }
                },

                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Status chart error:", error);
        showChartError("statusChart");
        throw error;
    }
}


/* =========================================
   7. PRIORITY CHART
========================================= */

async function loadPriorityChart() {
    try {
        const response = await apiRequest(
            "/dashboard/priority-counts"
        );

        const data = extractData(response) || [];

        const labels = data.map(item =>
            formatLabel(item.priority)
        );

        const values = data.map(item =>
            Number(item.count) || 0
        );

        const colors = data.map(item => {
            const priority = String(item.priority || "").toUpperCase();

            const colorMap = {
                CRITICAL: "#d94d4d",
                HIGH: "#e69a32",
                MEDIUM: "#376bd6",
                LOW: "#299b55"
            };

            return colorMap[priority] || "#168b9c";
        });

        const canvas = document.getElementById("priorityChart");

        if (!canvas) return;

        if (priorityChartInstance) {
            priorityChartInstance.data.labels = labels;
            priorityChartInstance.data.datasets[0].data = values;
            priorityChartInstance.data.datasets[0].backgroundColor = colors;
            priorityChartInstance.update();
            return;
        }

        priorityChartInstance = new Chart(canvas, {
            type: "doughnut",

            data: {
                labels: labels,

                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });

    } catch (error) {
        console.error("Priority chart error:", error);
        showChartError("priorityChart");
        throw error;
    }
}


/* =========================================
   8. TEAM WORKLOAD CHART
========================================= */

async function loadTeamWorkloadChart() {
    try {
        const response = await apiRequest(
            "/dashboard/team-workload"
        );

        const data = extractData(response) || [];

        const labels = data.map(item =>
            item.team_name || "Unassigned"
        );

        const openValues = data.map(item =>
            Number(item.open_complaints) || 0
        );

        const closedValues = data.map(item =>
            Number(item.closed_complaints) || 0
        );

        const canvas = document.getElementById(
            "teamWorkloadChart"
        );

        if (!canvas) return;

        if (teamWorkloadChartInstance) {
            teamWorkloadChartInstance.data.labels = labels;
            teamWorkloadChartInstance.data.datasets[0].data = openValues;
            teamWorkloadChartInstance.data.datasets[1].data = closedValues;
            teamWorkloadChartInstance.update();
            return;
        }

        teamWorkloadChartInstance = new Chart(canvas, {
            type: "bar",

            data: {
                labels: labels,

                datasets: [
                    {
                        label: "Open Complaints",
                        data: openValues,
                        backgroundColor: "#e69a32",
                        borderRadius: 5
                    },
                    {
                        label: "Closed Complaints",
                        data: closedValues,
                        backgroundColor: "#299b55",
                        borderRadius: 5
                    }
                ]
            },

            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom"
                    }
                },

                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Team workload chart error:", error);
        showChartError("teamWorkloadChart");
        throw error;
    }
}


/* =========================================
   9. DECISION OVERVIEW CHART
========================================= */

async function loadDecisionChart() {
    try {
        const response = await apiRequest(
            "/dashboard/decision-counts"
        );

        const data = extractData(response) || [];

        const labels = data.map(item =>
            formatLabel(item.decision_type)
        );

        const values = data.map(item =>
            Number(item.count) || 0
        );

        const canvas = document.getElementById("decisionChart");

        if (!canvas) return;

        if (decisionChartInstance) {
            decisionChartInstance.data.labels = labels;
            decisionChartInstance.data.datasets[0].data = values;
            decisionChartInstance.update();
            return;
        }

        decisionChartInstance = new Chart(canvas, {
            type: "bar",

            data: {
                labels: labels,

                datasets: [{
                    label: "Complaints",
                    data: values,
                    backgroundColor: [
                        "#168b9c",
                        "#d94d4d",
                        "#e69a32",
                        "#8059d8",
                        "#376bd6"
                    ],
                    borderRadius: 6,
                    barThickness: 40
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display: false
                    }
                },

                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Decision chart error:", error);
        showChartError("decisionChart");
        throw error;
    }
}


/* =========================================
   10. RECENT COMPLAINTS TABLE
========================================= */

async function loadRecentComplaints() {
    const tableBody = document.getElementById(
        "recentComplaintsTable"
    );

    if (!tableBody) return;

    try {
        const response = await apiRequest(
            "/dashboard/recent-complaints?limit=10"
        );

        const complaints = extractData(response) || [];

        if (!Array.isArray(complaints) || complaints.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center">
                        No complaints found.
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = complaints.map(complaint => {
            const priority = String(
                complaint.priority || "Not Assigned"
            ).toLowerCase();

            const status = formatLabel(
                complaint.complaint_status || "Unknown"
            );

            return `
                <tr>
                    <td>
                        <span class="complaint-number">
                            ${escapeHTML(complaint.complaint_number || "-")}
                        </span>
                    </td>

                    <td>
                        ${escapeHTML(complaint.serial_number || "-")}
                    </td>

                    <td>
                        <span class="complaint-model">
                            ${escapeHTML(complaint.model_number || "-")}
                        </span>
                    </td>

                    <td>
                        <span class="complaint-customer">
                            ${escapeHTML(complaint.customer_name || "-")}
                        </span>
                    </td>

                    <td>
                        ${escapeHTML(
                            complaint.issue_type_name ||
                            complaint.reported_issue ||
                            "-"
                        )}
                    </td>

                    <td>
                        <span class="priority-badge ${escapeHTML(priority)}">
                            ${escapeHTML(formatLabel(priority))}
                        </span>
                    </td>

                    <td>
                        <span class="status-badge">
                            ${escapeHTML(status)}
                        </span>
                    </td>

                    <td>
                        ${escapeHTML(formatDate(complaint.registered_at))}
                    </td>
                </tr>
            `;
        }).join("");

    } catch (error) {
        console.error("Recent complaints error:", error);

        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-danger">
                    Unable to load recent complaints.
                </td>
            </tr>
        `;

        throw error;
    }
}


/* =========================================
   11. REFRESH BUTTON
========================================= */

function setRefreshButtonLoading(isLoading) {
    const button = document.getElementById(
        "refreshDashboardBtn"
    );

    if (!button) return;

    button.disabled = isLoading;
    button.classList.toggle("loading", isLoading);

    button.innerHTML = isLoading
        ? `<i class="bi bi-arrow-clockwise me-2"></i>Refreshing...`
        : `<i class="bi bi-arrow-clockwise me-2"></i>Refresh`;
}


/* =========================================
   12. COMMON HELPERS
========================================= */

function setElementText(elementId, value) {
    const element = document.getElementById(elementId);

    if (element) {
        element.textContent = value ?? 0;
    }
}


function formatLabel(value) {
    if (!value) return "Unknown";

    return String(value)
        .toLowerCase()
        .replace(/_/g, " ")
        .replace(/\b\w/g, character => character.toUpperCase());
}


function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => {
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


function showChartError(chartId) {
    const canvas = document.getElementById(chartId);

    if (!canvas) return;

    const container = canvas.parentElement;

    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <span class="text-muted">
                Unable to load chart data.
            </span>
        </div>
    `;
}
