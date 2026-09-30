import { RISK_LEVELS, STATUSES, STATUS_LABEL } from "../services/format.js";

export default function Filters({ filters, setFilters, search, setSearch, rules, view, setView }) {
  const set = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));
  const hasFilters = search || Object.values(filters).some(Boolean);
  return (
    <div className="filters">
      <div className="segmented" role="tablist" aria-label="Which transactions to list">
        {[["flagged", "Flagged"], ["all", "All transactions"]].map(([v, l]) => (
          <button key={v} role="tab" aria-selected={view === v} className={view === v ? "active" : ""} onClick={() => setView(v)}>{l}</button>
        ))}
      </div>
      <input type="search" placeholder="Search transaction or customer ID" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search" />
      <select value={filters.risk_level} onChange={set("risk_level")} aria-label="Risk level">
        <option value="">All risk levels</option>{RISK_LEVELS.map((l) => <option key={l}>{l}</option>)}
      </select>
      <select value={filters.status} onChange={set("status")} aria-label="Status">
        <option value="">All statuses</option>{STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
      </select>
      <select value={filters.rule} onChange={set("rule")} aria-label="Rule">
        <option value="">All rules</option>{rules.map((r) => <option key={r.name} value={r.name}>{r.display_name}</option>)}
      </select>
      <input type="date" value={filters.date} onChange={set("date")} aria-label="Date (UTC)" />
      {hasFilters && <button className="btn ghost" onClick={() => { setSearch(""); setFilters({ risk_level: "", status: "", rule: "", date: "" }); }}>Reset filters</button>}
    </div>
  );
}
