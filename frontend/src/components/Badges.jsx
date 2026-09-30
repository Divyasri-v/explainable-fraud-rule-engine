import { ESCALATION_LABEL, RISK_LEVELS, STATUS_LABEL } from "../services/format.js";

export function RiskBadge({ level }) {
  return <span className={`badge risk-${level.toLowerCase()}`}>{level}</span>;
}

export function StatusBadge({ status }) {
  return <span className={`badge status-${status.toLowerCase()}`}>{STATUS_LABEL[status] || status}</span>;
}

export function EscalationBadge({ status }) {
  if (!status || status === "NOT ESCALATED") return null;
  const cls = status.toLowerCase().replace(/ /g, "-");
  return <span className={`badge escalation-${cls}`}>🚨 {ESCALATION_LABEL[status] || status}</span>;
}

/* Four-segment meter: filled segments match the risk level, so severity reads without colour alone. */
export function RiskMeter({ score, level }) {
  const filled = RISK_LEVELS.indexOf(level) + 1;
  return (
    <span className="meter" title={`${score}/100 — ${level}`}>
      <span className="meter-score">{score}</span>
      <span className="meter-bars" aria-hidden="true">
        {RISK_LEVELS.map((l, i) => (
          <i key={l} className={i < filled ? `on risk-${level.toLowerCase()}-fill` : ""} />
        ))}
      </span>
    </span>
  );
}
