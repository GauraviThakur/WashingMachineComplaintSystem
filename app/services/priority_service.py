
from typing import Final


ISSUE_TYPE_PRIORITIES: Final[dict[str, str]] = {
    "machine not starting": "HIGH",
    "power failure": "HIGH",
    "control panel failure": "HIGH",
    "voltage abnormality": "HIGH",
    "abnormal noise": "MEDIUM",
    "excessive vibration": "HIGH",
    "drum not rotating": "HIGH",
    "water leakage": "HIGH",
    "drainage problem": "HIGH",
    "poor washing performance": "MEDIUM",
    "water not filling": "MEDIUM",
    "water not heating": "MEDIUM",
    "installation defect": "LOW",
}


CRITICAL_KEYWORDS: Final[tuple[str, ...]] = (
    "electric shock",
    "electrical shock",
    "burning smell",
    "burning wire",
    "smoke",
    "sparks",
    "sparking",
    "short circuit",
    "overheating",
    "fire",
    "flames",
    "exposed wire",
    "current leakage",
)


HIGH_KEYWORDS: Final[tuple[str, ...]] = (
    "major water leakage",
    "heavy water leakage",
    "water flooding",
    "water overflowing",
    "machine not starting",
    "power failure",
    "voltage abnormality",
    "control panel failure",
    "drum not rotating",
    "not draining",
    "drainage failure",
    "drainage problem",
    "water remains in drum",
    "water remains inside drum",
    "water remains inside the drum",
    "water not draining",
    "water is not draining",
    "water does not drain",
    "water not being drained",
    "drainage system is not removing water",
    "drainage system not working",
    "failure to drain",
    "drum not emptying",
    "excessive vibration",
    "severe vibration",
    "motor failure",
    "pump failure",
    "machine stops during operation",
)


LOW_KEYWORDS: Final[tuple[str, ...]] = (
    "minor scratch",
    "minor dent",
    "cosmetic damage",
    "paint peeling",
    "surface scratch",
    "discoloration",
    "minor finishing defect",
    "loose external panel",
)


def determine_complaint_priority(
    *,
    reported_issue: str,
    issue_type_name: str | None = None,
) -> str:
    """Determine complaint priority from safety indicators and issue type."""

    issue_text = (reported_issue or "").strip().casefold()
    issue_type = (issue_type_name or "").strip().casefold()

    combined_text = f"{issue_type} {issue_text}"

    # Safety-related problems always receive the highest priority.
    if any(keyword in combined_text for keyword in CRITICAL_KEYWORDS):
        return "CRITICAL"

    # Explicitly minor cosmetic problems receive low priority.
    if any(keyword in combined_text for keyword in LOW_KEYWORDS):
        return "LOW"

    # Serious functional failures receive high priority.
    if any(keyword in combined_text for keyword in HIGH_KEYWORDS):
        return "HIGH"

    # Use the configured default priority for the issue type.
    return ISSUE_TYPE_PRIORITIES.get(issue_type, "MEDIUM")
