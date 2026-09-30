export const inr = (n) => "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const fmtTime = (iso) =>
  new Date(iso).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" });
export const fmtHour = (iso) => new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
export const RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
export const STATUSES = ["NORMAL", "FLAGGED", "REVIEWED", "CLEARED"];
export const STATUS_LABEL = { NORMAL: "Normal", FLAGGED: "Pending review", REVIEWED: "Reviewed", CLEARED: "Cleared" };
export const RISK_COLOR = { LOW: "var(--low)", MEDIUM: "var(--medium)", HIGH: "var(--high)", CRITICAL: "var(--critical)" };
export const ESCALATION_STATUSES = ["NOT ESCALATED", "ESCALATION PENDING", "ESCALATED", "UNDER INVESTIGATION", "RESOLVED"];
export const ESCALATION_LABEL = {
  "NOT ESCALATED": "Not escalated",
  "ESCALATION PENDING": "Escalation pending",
  "ESCALATED": "Escalated to Cyber Crime",
  "UNDER INVESTIGATION": "Under investigation",
  "RESOLVED": "Resolved",
};
