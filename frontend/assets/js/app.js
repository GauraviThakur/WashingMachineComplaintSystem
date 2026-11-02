
/* =========================================
   APPLICATION CONFIGURATION
========================================= */

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";


/* =========================================
   ERROR MESSAGE HANDLING
========================================= */

function extractErrorMessage(errorData, status) {
    const detail = errorData?.detail;

    // Handle a simple string error.
    if (typeof detail === "string" && detail.trim()) {
        return detail;
    }

    // Handle an object-based error returned by FastAPI.
    if (detail && typeof detail === "object") {

        // Handle validation errors returned as an array.
        if (Array.isArray(detail)) {
            return detail
                .map(item => {
                    if (typeof item === "string") {
                        return item;
                    }

                    if (item?.msg) {
                        const field = Array.isArray(item.loc)
                            ? item.loc[item.loc.length - 1]
                            : null;

                        return field
                            ? `${field}: ${item.msg}`
                            : item.msg;
                    }

                    return JSON.stringify(item);
                })
                .join("; ");
        }

        if (typeof detail.message === "string") {
            let message = detail.message;

            const existingComplaint = detail.existing_complaint;

            if (existingComplaint?.complaint_number) {
                message +=
                    ` Existing complaint number: ${existingComplaint.complaint_number}.`;
            }

            if (existingComplaint?.complaint_status) {
                message +=
                    ` Status: ${existingComplaint.complaint_status}.`;
            }

            return message;
        }

        return JSON.stringify(detail);
    }

    // Handle a message at the root level.
    if (
        typeof errorData?.message === "string" &&
        errorData.message.trim()
    ) {
        return errorData.message;
    }

    return `Request failed with status ${status}. Please try again.`;
}


/* =========================================
   COMMON API REQUEST FUNCTION
========================================= */

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options
        });

        // Read the response body only once.
        const responseText = await response.text();

        let responseData = null;

        if (responseText) {
            try {
                responseData = JSON.parse(responseText);
            } catch {
                responseData = responseText;
            }
        }

        if (!response.ok) {
            let errorMessage;

            if (
                responseData &&
                typeof responseData === "object"
            ) {
                errorMessage = extractErrorMessage(
                    responseData,
                    response.status
                );
            } else if (
                typeof responseData === "string" &&
                responseData.trim()
            ) {
                errorMessage = responseData;
            } else {
                errorMessage =
                    `Request failed with status ${response.status}.`;
            }

            throw new Error(errorMessage);
        }

        return responseData;

    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
}


/* =========================================
   NOTIFICATION MESSAGE
========================================= */

function showNotification(message, type = "success") {
    const notification = document.createElement("div");

    notification.className = `app-notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3500);
}


/* =========================================
   DATE FORMATTING
========================================= */

function formatDate(dateValue) {
    if (!dateValue) {
        return "-";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
        return "-";
    }

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}
