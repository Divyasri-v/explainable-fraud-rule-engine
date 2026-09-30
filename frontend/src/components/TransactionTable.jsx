import { RiskBadge, RiskMeter, StatusBadge } from "./Badges.jsx";
import { fmtTime, inr } from "../services/format.js";

export default function TransactionTable({ rows, rules, loading, onOpen, onAction, busyId }) {
  const label = (n) => rules.find((r) => r.name === n)?.display_name || n;
  if (loading && rows.length === 0) return <div className="empty">Loading transactions…</div>;
  if (rows.length === 0)
    return <div className="empty"><strong>No transactions match.</strong><br />Adjust the filters, or use “Generate demo transactions” to create sample activity.</div>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Transaction</th><th>Customer</th><th className="num">Amount</th><th>Location</th><th>Time</th><th>Risk</th><th>Level</th><th>Triggered rules</th><th>Status</th><th>Action</th></tr>
        </thead>
        <tbody>
          {rows.map((t) => {
            const canReview = t.status === "FLAGGED";
            const canClear = t.status === "FLAGGED" || t.status === "REVIEWED";
            return (
              <tr key={t.transaction_id} onClick={() => onOpen(t.transaction_id)} className="clickable">
                <td><button className="link" onClick={(e) => { e.stopPropagation(); onOpen(t.transaction_id); }}>{t.transaction_id}</button></td>
                <td>{t.customer_id}</td>
                <td className="num">{inr(t.amount)}</td>
                <td>{t.city || "—"}</td>
                <td className="nowrap">{fmtTime(t.timestamp)}</td>
                <td><RiskMeter score={t.risk_score} level={t.risk_level} /></td>
                <td><RiskBadge level={t.risk_level} /></td>
                <td>{t.flags.length ? t.flags.map((f) => <span key={f.id} className="chip">{label(f.rule_name)}</span>) : <span className="muted">None</span>}</td>
                <td><StatusBadge status={t.status} /></td>
                <td onClick={(e) => e.stopPropagation()} className="nowrap">
                  {canReview || canClear ? (
                    <>
                      {canReview && <button className="btn sm" disabled={busyId === t.transaction_id} onClick={() => onAction(t.transaction_id, "review")}>Review</button>}{" "}
                      {canClear && <button className="btn sm ok" disabled={busyId === t.transaction_id} onClick={() => onAction(t.transaction_id, "clear")}>Clear</button>}
                    </>
                  ) : <button className="btn sm ghost" onClick={() => onOpen(t.transaction_id)}>Details</button>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
