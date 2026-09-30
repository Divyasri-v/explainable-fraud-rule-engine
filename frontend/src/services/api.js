const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  } catch {
    throw new Error(`Cannot reach the API at ${BASE}. Start the backend and check VITE_API_URL.`);
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
      else if (Array.isArray(body.detail)) msg = body.detail.map((d) => `${d.loc.slice(1).join(".")}: ${d.msg}`).join("; ");
    } catch { /* keep default message */ }
    throw new Error(msg);
  }
  return res.json();
}

const qs = (params = {}) => {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== "" && v != null && p.set(k, v));
  const s = p.toString();
  return s ? `?${s}` : "";
};

export const api = {
  stats: () => request("/dashboard/stats"),
  rules: () => request("/rules"),
  notifications: () => request("/notifications"),
  transactions: (params) => request(`/transactions${qs(params)}`),
  flagged: (params) => request(`/transactions/flagged${qs(params)}`),
  detail: (id) => request(`/transactions/${encodeURIComponent(id)}`),
  review: (id, body) => request(`/transactions/${encodeURIComponent(id)}/review`, { method: "POST", body: JSON.stringify(body) }),
  clear: (id, body) => request(`/transactions/${encodeURIComponent(id)}/clear`, { method: "POST", body: JSON.stringify(body) }),
  generateDemo: () => request("/demo/generate", { method: "POST" }),
};
