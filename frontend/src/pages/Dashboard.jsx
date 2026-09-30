import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../services/api.js";
import SummaryCards from "../components/SummaryCards.jsx";
import Charts from "../components/Charts.jsx";
import Filters from "../components/Filters.jsx";
import TransactionTable from "../components/TransactionTable.jsx";
import TransactionModal from "../components/TransactionModal.jsx";
import { AlertsPanel, RulesPanel } from "../components/SidePanels.jsx";

const EMPTY = { risk_level: "", status: "", rule: "", date: "" };

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [rules, setRules] = useState([]);
  const [rows, setRows] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [filters, setFilters] = useState(EMPTY);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [view, setView] = useState("flagged");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [toast, setToast] = useState("");
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");
  const timer = useRef();

  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem("theme", theme); }, [theme]);
  useEffect(() => { const t = setTimeout(() => setQuery(search), 300); return () => clearTimeout(t); }, [search]);
  const notify = useCallback((msg) => { setToast(msg); clearTimeout(timer.current); timer.current = setTimeout(() => setToast(""), 3500); }, []);

  const load = useCallback(async () => {
    try {
      const params = { ...filters, search: query };
      const [s, list, n] = await Promise.all([
        api.stats(),
        view === "flagged"
          ? api.flagged(params)
          : view === "escalated"
          ? api.transactions({ ...params, escalated_only: true })
          : api.transactions(params),
        api.notifications(),
      ]);
      setStats(s); setRows(list); setAlerts(n); setError("");
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }, [filters, query, view]);

  useEffect(() => { api.rules().then(setRules).catch(() => {}); }, []);
  useEffect(() => { setLoading(true); load(); }, [load]);
  useEffect(() => { const t = setInterval(load, 15000); return () => clearInterval(t); }, [load]);

  const generate = async () => {
    setGenerating(true);
    try {
      const r = await api.generateDemo();
      const crit = r.scenarios.filter((s) => s.risk_level === "CRITICAL").length;
      notify(`Generated ${r.scenarios.length} demo scenarios${crit ? ` · ${crit} critical alert sent` : ""}`);
      await load();
    } catch (e) { setError(e.message); } finally { setGenerating(false); }
  };

  const quickAction = async (id, kind) => {
    setBusyId(id);
    try { await api[kind](id, { reviewer: "analyst", comments: null }); notify(kind === "review" ? `${id} marked as reviewed` : `${id} cleared`); await load(); }
    catch (e) { setError(e.message); } finally { setBusyId(null); }
  };

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <h1>Fraud Review Console</h1>
          <p className="muted">Rule-based scoring with explainable flags. {stats?.demo_mode && <span className="chip">DEMO DATA · not real financial information</span>}</p>
        </div>
        <div className="top-actions">
          <button className="btn ghost" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>{theme === "light" ? "Dark mode" : "Light mode"}</button>
          <button className="btn primary" onClick={generate} disabled={generating}>{generating ? "Generating…" : "Generate demo transactions"}</button>
        </div>
      </header>

      {error && <div className="alert error" role="alert">{error} <button className="link" onClick={load}>Retry</button></div>}

      <SummaryCards stats={stats} />
      <Charts stats={stats} rules={rules} />

      <div className="main-grid">
        <section className="card table-card">
          <h3>{view === "flagged" ? "Flagged transactions" : "All transactions"} <span className="muted">({rows.length})</span></h3>
          <Filters filters={filters} setFilters={setFilters} search={search} setSearch={setSearch} rules={rules} view={view} setView={setView} />
          <TransactionTable rows={rows} rules={rules} loading={loading} onOpen={setSelected} onAction={quickAction} busyId={busyId} />
        </section>
        <aside className="side">
          <AlertsPanel items={alerts} demoMode={stats?.demo_mode} onOpen={setSelected} />
          <RulesPanel rules={rules} />
        </aside>
      </div>

      {selected && <TransactionModal id={selected} rules={rules} onClose={() => setSelected(null)} onChanged={load} notify={notify} />}
      {toast && <div className="toast" role="status">{toast}</div>}
    </div>
  );
}
