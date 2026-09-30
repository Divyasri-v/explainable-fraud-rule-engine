import { useEffect, useState } from "react";
import { api } from "../services/api.js";
import { RiskBadge, RiskMeter, StatusBadge } from "./Badges.jsx";
import { fmtTime, inr } from "../services/format.js";

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

  const label = (n) => rules.find((r) => r.name === n)?.display_name || n;
  const canReview = txn?.status === "FLAGGED";
  const canClear = txn && (txn.status === "FLAGGED" || txn.status === "REVIEWED");

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Transaction details" onClick={(e) => e.stopPropagation()}>
        <header className="modal-head">
          <div><h2>{id}</h2><span className="muted">Transaction details</span></div>
          <button className="btn ghost" onClick={onClose} aria-label="Close">Close</button>
        </header>

        {error && <div className="alert error" role="alert">{error}</div>}
        {!txn && !error && <div className="empty">Loading…</div>}

        {txn && (
          <div className="modal-body">
            <dl className="facts">
              <div><dt>Customer ID</dt><dd>{txn.customer_id}</dd></div>
              <div><dt>Amount</dt><dd>{inr(txn.amount)}</dd></div>
              <div><dt>Merchant</dt><dd>{txn.merchant || "—"}</dd></div>
              <div><dt>Timestamp</dt><dd>{fmtTime(txn.timestamp)}</dd></div>
              <div><dt>Location</dt><dd>{txn.city || "—"} <span className="muted">({txn.latitude.toFixed(3)}, {txn.longitude.toFixed(3)})</span></dd></div>
              <div><dt>Risk score</dt><dd><RiskMeter score={txn.risk_score} level={txn.risk_level} /> <RiskBadge level={txn.risk_level} /></dd></div>
              <div><dt>Current status</dt><dd><StatusBadge status={txn.status} /></dd></div>
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

            <section className="review-box">
              <h3>Your decision</h3>
              <div className="row">
                <label>Reviewer<input value={reviewer} maxLength={80} onChange={(e) => setReviewer(e.target.value)} /></label>
              </div>
              <label>Comment (optional)
                <textarea rows={3} maxLength={1000} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="What did you check? Why is this fraud or safe?" />
              </label>
              <div className="actions">
                <button className="btn" disabled={busy || !canReview} onClick={() => act("review")}>Mark as reviewed</button>
                <button className="btn ok" disabled={busy || !canClear} onClick={() => act("clear")}>Clear transaction</button>
                {!canReview && !canClear && <span className="muted">{txn.status === "CLEARED" ? "Already cleared." : "Only flagged transactions need a decision."}</span>}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
