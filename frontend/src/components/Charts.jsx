import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { RISK_LEVELS, fmtHour } from "../services/format.js";

const COLORS = { LOW: "#2f855a", MEDIUM: "#b7791f", HIGH: "#d9541e", CRITICAL: "#b4233c" };
const axis = { fontSize: 12, fill: "var(--muted)" };
const tip = { contentStyle: { background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 6, color: "var(--ink)" } };

export default function Charts({ stats, rules }) {
  if (!stats) return null;
  const byLevel = RISK_LEVELS.map((l) => ({ level: l, count: stats.by_risk_level[l] || 0 }));
  const label = (name) => rules.find((r) => r.name === name)?.display_name || name;
  const byRule = Object.entries(stats.flags_by_rule).map(([name, count]) => ({ rule: label(name), count }));
  const activity = stats.activity.map((a) => ({ ...a, label: fmtHour(a.hour) }));

  return (
    <section className="charts">
      <div className="card">
        <h3>Transactions by risk level</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={byLevel}>
            <CartesianGrid stroke="var(--line)" vertical={false} />
            <XAxis dataKey="level" tick={axis} /><YAxis allowDecimals={false} tick={axis} width={36} />
            <Tooltip {...tip} cursor={{ fill: "var(--hover)" }} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>{byLevel.map((d) => <Cell key={d.level} fill={COLORS[d.level]} />)}</Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="card">
        <h3>Fraud flags by rule</h3>
        {byRule.length === 0 ? <p className="empty-sm">No flags yet.</p> : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byRule} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid stroke="var(--line)" horizontal={false} />
              <XAxis type="number" allowDecimals={false} tick={axis} />
              <YAxis type="category" dataKey="rule" tick={axis} width={150} />
              <Tooltip {...tip} cursor={{ fill: "var(--hover)" }} />
              <Bar dataKey="count" fill="var(--brand)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      <div className="card">
        <h3>Recent activity (24h)</h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={activity}>
            <CartesianGrid stroke="var(--line)" vertical={false} />
            <XAxis dataKey="label" tick={axis} interval={5} /><YAxis allowDecimals={false} tick={axis} width={36} />
            <Tooltip {...tip} /><Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="total" name="Transactions" stroke="var(--brand)" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="flagged" name="Flagged" stroke="#b4233c" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
