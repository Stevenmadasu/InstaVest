/**
 * InstaVest API Client
 * Centralized HTTP client for backend communication.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }
  return res.json();
}

// ─── Companies ─────────────────────────────────────
export const api = {
  health: () => fetchAPI("/health"),

  // Companies
  searchCompanies: (q: string) => fetchAPI(`/companies/search?q=${encodeURIComponent(q)}`),
  getCompany: (ticker: string) => fetchAPI(`/companies/${ticker}`),
  getResearch: (ticker: string) => fetchAPI(`/companies/${ticker}/research`),
  refreshCompany: (ticker: string) => fetchAPI(`/companies/${ticker}/refresh`, { method: "POST" }),
  getPrices: (ticker: string) => fetchAPI(`/companies/${ticker}/prices`),
  getFinancials: (ticker: string) => fetchAPI(`/companies/${ticker}/financials`),
  getCompanySignals: (ticker: string) => fetchAPI(`/companies/${ticker}/signals`),

  // Watchlists
  getWatchlists: () => fetchAPI("/watchlists"),
  createWatchlist: (name: string) => fetchAPI("/watchlists", { method: "POST", body: JSON.stringify({ name }) }),
  addToWatchlist: (id: number, ticker: string) =>
    fetchAPI(`/watchlists/${id}/items`, { method: "POST", body: JSON.stringify({ ticker }) }),
  removeFromWatchlist: (id: number, ticker: string) =>
    fetchAPI(`/watchlists/${id}/items/${ticker}`, { method: "DELETE" }),

  // Portfolios
  getPortfolios: () => fetchAPI("/portfolios"),
  createPortfolio: (name: string) => fetchAPI("/portfolios", { method: "POST", body: JSON.stringify({ name }) }),
  getPortfolio: (id: number) => fetchAPI(`/portfolios/${id}`),
  addHolding: (id: number, data: { ticker: string; shares: number; average_cost: number }) =>
    fetchAPI(`/portfolios/${id}/holdings`, { method: "POST", body: JSON.stringify(data) }),

  // Thesis
  getThesisBoards: () => fetchAPI("/thesis-boards"),
  createThesisBoard: (data: { title: string; description?: string; time_horizon?: string }) =>
    fetchAPI("/thesis-boards", { method: "POST", body: JSON.stringify(data) }),
  getThesisBoard: (id: number) => fetchAPI(`/thesis-boards/${id}`),
  addAssumption: (boardId: number, data: { assumption_text: string; linked_metric?: string }) =>
    fetchAPI(`/thesis-boards/${boardId}/assumptions`, { method: "POST", body: JSON.stringify(data) }),

  // Signals
  getSignals: (params?: { ticker?: string; signal_type?: string; severity?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return fetchAPI(`/signals${qs ? `?${qs}` : ""}`);
  },

  // Reports
  getReports: () => fetchAPI("/reports"),
  getReport: (id: number) => fetchAPI(`/reports/${id}`),
  generateReport: (data: { ticker?: string; report_type: string }) =>
    fetchAPI("/reports/generate", { method: "POST", body: JSON.stringify(data) }),

  // ─── Temporal Intelligence ──────────────────────────
  getIntelligenceStream: (limit: number = 30, hours: number = 48) =>
    fetchAPI<any>(`/api/temporal/stream?limit=${limit}&hours=${hours}`),
  triggerDailyPipeline: () =>
    fetchAPI<any>(`/api/temporal/pipeline/trigger`, { method: "POST" }),
  getLatestDailySnapshot: () =>
    fetchAPI<any>(`/api/temporal/snapshot/latest`),
};
