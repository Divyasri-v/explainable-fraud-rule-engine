import { useEffect, useState } from "react";
import { api } from "../services/api.js";
import { EscalationBadge, RiskBadge, RiskMeter, StatusBadge } from "./Badges.jsx";
import { ESCALATION_LABEL, fmtTime, inr } from "../services/format.js";

export default function TransactionModal({ id, rules, onClose, onChanged, notify }) {
  const [txn, setTxn] = useState(null);
  const [error, setError] = useState("");
  const [comment, setComment] = useState("");
  const [reviewer, setReviewer] = useState("analyst");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setTxn(null); setError("");
    api.detail(id).then(setTxn).catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const act = async (kind) => {
    setBusy(true);
    try {
      const updated = await api[kind](id, { reviewer: reviewer.trim() || "analyst", comments: comment.trim() || null });
      setTxn(updated); setComment("");
      notify(kind === "review" ? `${id} marked as reviewed` : `${id} cleared`);
      onChanged();
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  const escalate = async () => {
    setBusy(true);
    try {
      const updated = await api.escalate(id, {
        reviewer: reviewer.trim() || "analyst",
        reason: comment.trim() || null,
        destination: "CYBER_CRIME"
      });
      setTxn(updated); setComment("");
      notify("Case successfully escalated to Cyber Crime Investigation Queue.");
      onChanged();
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  const updateEscalationStatus = async (newStatus) => {
    setBusy(true);
    try {
      const updated = await api.updateEscalationStatus(id, { status: newStatus, notes: comment.trim() || null });
      setTxn(updated); setComment("");
      notify(`Escalation status updated to ${newStatus}`);
      onChanged();
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  const label = (n) => rules.find((r) => r.name === n)?.display_name || n;
  const canReview = txn?.status === "FLAGGED";
  const canClear = txn && (txn.status === "FLAGGED" || txn.status === "REVIEWED");
  const isHighOrCritical = txn && (txn.risk_level === "HIGH" || txn.risk_level === "CRITICAL");
  const canEscalate = isHighOrCritical && (txn.escalation_status === "NOT ESCALATED" || !txn.escalation_status);

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Transaction details" onClick={(e) => e.stopPropagation()}>
        <header className="modal-head">
          <div>
            <h2>{id}</h2>
            <span className="muted">Transaction details</span>
          </div>
          <button className="btn ghost" onClick={onClose} aria-label="Close">Close</button>
        </header>

        {error && <div className="alert error" role="alert">{error}</div>}
        {!txn && !error && <div className="empty">Loading…</div>}

        {txn && (
          <div className="modal-body">
            {isHighOrCritical && (
              <div className={`alert-banner alert-banner-${txn.risk_level.toLowerCase()}`}>
                <div className="alert-banner-head">
                  <span className="alert-icon">🚨</span>
                  <div>
                    <strong style={{ fontSize: "15px" }}>{txn.risk_level} FRAUD ALERT</strong>
                    <div className="small">Transaction requires immediate attention. Eligible for Cyber Crime escalation.</div>
                  </div>
                </div>
                <div className="alert-banner-details">
                  <span><strong>Transaction ID:</strong> {txn.transaction_id}</span>
                  <span><strong>Customer:</strong> {txn.customer_id}</span>
                  <span><strong>Risk Score:</strong> {txn.risk_score}/100</span>
                  <span><strong>Risk Level:</strong> {txn.risk_level}</span>
                  <span><strong>Escalation:</strong> {txn.escalation_status || "NOT ESCALATED"}</span>
                </div>
              </div>
            )}

            <dl className="facts">
              <div><dt>Customer ID</dt><dd>{txn.customer_id}</dd></div>
              <div><dt>Amount</dt><dd>{inr(txn.amount)}</dd></div>
              <div><dt>Merchant</dt><dd>{txn.merchant || "—"}</dd></div>
              <div><dt>Timestamp</dt><dd>{fmtTime(txn.timestamp)}</dd></div>
              <div><dt>Location</dt><dd>{txn.city || "—"} <span className="muted">({txn.latitude.toFixed(3)}, {txn.longitude.toFixed(3)})</span></dd></div>
              <div><dt>Risk score</dt><dd><RiskMeter score={txn.risk_score} level={txn.risk_level} /> <RiskBadge level={txn.risk_level} /></dd></div>
              <div><dt>Review status</dt><dd><StatusBadge status={txn.status} /></dd></div>
              <div><dt>Escalation status</dt><dd>{txn.escalation_status && txn.escalation_status !== "NOT ESCALATED" ? <EscalationBadge status={txn.escalation_status} /> : <span className="muted">NOT ESCALATED</span>}</dd></div>
            </dl>

            <section className="explain">
              <h3>Rule explanation</h3>
              <p className="explain-head">{txn.explanation.headline}</p>
              {txn.explanation.lines.length > 0 && <ul>{txn.explanation.lines.map((l, i) => <li key={i}>{l}</li>)}</ul>}
            </section>

            <section>
              <h3>Triggered fraud rules</h3>
              {txn.flags.length === 0 ? <p className="muted">No rules triggered.</p> : txn.flags.map((f) => (
                <div key={f.id} className="rule-hit">
                  <div className="rule-hit-top"><strong>✓ {label(f.rule_name)}</strong><span className="points">+{f.risk_points}</span></div>
                  <p>Reason: {f.reason}</p>
                  <p className="muted">Risk points: +{f.risk_points}</p>
                </div>
              ))}
            </section>

            {txn.escalations && txn.escalations.length > 0 && (
              <section className="escalation-history">
                <h3>Escalation History</h3>
                <div className="history-list">
                  {txn.escalations.map((esc) => (
                    <div key={esc.id} className="history-item">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <strong>🚨 {esc.destination === "CYBER_CRIME" ? "Escalated to Cyber Crime Investigation Queue" : esc.destination}</strong>
                        <EscalationBadge status={esc.status} />
                      </div>
                      <p className="small muted" style={{ marginTop: "4px" }}>Escalated by: <strong>{esc.escalated_by}</strong> on {fmtTime(esc.escalated_at || esc.created_at)}</p>
                      {esc.reason && <p className="small" style={{ marginTop: "2px" }}>Notes: {esc.reason}</p>}
                      {esc.triggered_rules && <p className="small muted" style={{ marginTop: "2px" }}>Triggered rules: {esc.triggered_rules}</p>}
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="review-box">
              <h3>Human Review & Escalation Decision</h3>
              <div className="row">
                <label>Reviewer<input value={reviewer} maxLength={80} onChange={(e) => setReviewer(e.target.value)} /></label>
              </div>
              <label>Comment / Escalation Note (optional)
                <textarea rows={3} maxLength={1000} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Provide rationale for review clearance or cyber crime escalation..." />
              </label>
              <div className="actions">
                <button className="btn" disabled={busy || !canReview} onClick={() => act("review")}>Mark as reviewed</button>
                <button className="btn ok" disabled={busy || !canClear} onClick={() => act("clear")}>Clear transaction</button>
                {canEscalate && (
                  <button className="btn primary" style={{ backgroundColor: "var(--critical)", borderColor: "var(--critical)", color: "#fff" }} disabled={busy} onClick={escalate}>
                    🚨 Escalate to Cyber Crime
                  </button>
                )}
                {!canReview && !canClear && !canEscalate && (
                  <span className="muted">
                    {txn.escalation_status && txn.escalation_status !== "NOT ESCALATED" ? `Case is ${txn.escalation_status}.` : txn.status === "CLEARED" ? "Already cleared." : "No decision required."}
                  </span>
                )}
              </div>

              {txn.escalation_status && txn.escalation_status !== "NOT ESCALATED" && (
                <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px dashed var(--line)" }}>
                  <div className="small muted" style={{ marginBottom: "6px" }}>Update Escalation Investigation Status:</div>
                  <div className="actions">
                    {["UNDER INVESTIGATION", "RESOLVED"].map((st) => (
                      <button key={st} className="btn sm ghost" disabled={busy || txn.escalation_status === st} onClick={() => updateEscalationStatus(st)}>
                        Mark {ESCALATION_LABEL[st] || st}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </section>

            <section>
              <h3>Recent history for {txn.customer_id}</h3>
              {txn.customer_history.length === 0 ? <p className="muted">No other transactions for this customer.</p> : (
                <div className="table-wrap"><table className="compact">
                  <thead><tr><th>Transaction</th><th className="num">Amount</th><th>Location</th><th>Time</th><th>Risk</th></tr></thead>
                  <tbody>{txn.customer_history.map((h) => (
                    <tr key={h.id}><td>{h.transaction_id}</td><td className="num">{inr(h.amount)}</td><td>{h.city || "—"}</td><td className="nowrap">{fmtTime(h.timestamp)}</td><td><RiskBadge level={h.risk_level} /></td></tr>
                  ))}</tbody>
                </table></div>
              )}
            </section>

            {txn.reviews.length > 0 && (
              <section>
                <h3>Review log</h3>
                {txn.reviews.map((r) => (
                  <p key={r.id} className="review-line"><strong>{r.action === "CLEARED" ? "Cleared" : "Reviewed"}</strong> by {r.reviewer} · {fmtTime(r.reviewed_at)}{r.comments ? ` — “${r.comments}”` : ""}</p>
                ))}
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
