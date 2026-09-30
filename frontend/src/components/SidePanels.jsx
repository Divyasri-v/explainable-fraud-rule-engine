import { fmtTime } from "../services/format.js";

export function AlertsPanel({ items, demoMode, onOpen }) {
  return (
    <div className="card">
      <h3>High-risk alerts {demoMode && <span className="chip">Demo mode: simulated</span>}</h3>
      {items.length === 0 ? <p className="empty-sm">No alerts yet. A transaction scoring 80 or more triggers one.</p> : (
        <ul className="plain">
          {items.map((n) => (
            <li key={n.id}>
              <button className="link" onClick={() => onOpen(n.txn_ref)}>{n.txn_ref}</button>
              <span className={`badge notif-${n.status.toLowerCase()}`}>{n.status === "SIMULATED" ? "Simulated" : n.status === "SENT" ? `Sent via ${n.channel}` : "Failed"}</span>
              <div className="muted small">{fmtTime(n.created_at)}{n.error ? ` · ${n.error}` : ""}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function RulesPanel({ rules }) {
  return (
    <div className="card">
      <h3>Active rules</h3>
      <ul className="plain">
        {rules.map((r) => (
          <li key={r.name}>
            <strong>{r.display_name}</strong> <span className="points">+{r.points}</span>
            <div className="muted small">{r.description}</div>
            <div className="small cfg">{Object.entries(r.config).filter(([k]) => k !== "points").map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`).join(" · ")}</div>
          </li>
        ))}
      </ul>
      <p className="muted small">Risk levels: 0–29 Low, 30–59 Medium, 60–79 High, 80+ Critical.</p>
    </div>
  );
}
