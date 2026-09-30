const CARDS = [
  { key: "total_transactions", label: "Total transactions" },
  { key: "flagged_transactions", label: "Flagged transactions" },
  { key: "high_risk", label: "High risk", tone: "high" },
  { key: "critical_risk", label: "Critical risk", tone: "critical" },
  { key: "cleared", label: "Cleared" },
  { key: "pending_review", label: "Pending review", tone: "pending" },
];

export default function SummaryCards({ stats }) {
  return (
    <section className="cards" aria-label="Summary">
      {CARDS.map((c) => (
        <div key={c.key} className={`card stat ${c.tone ? `tone-${c.tone}` : ""}`}>
          <span className="stat-label">{c.label}</span>
          <span className="stat-value">{stats ? stats[c.key].toLocaleString("en-IN") : "–"}</span>
        </div>
      ))}
    </section>
  );
}
