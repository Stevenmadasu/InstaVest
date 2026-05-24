"use client";
import { Briefcase, PieChart, TrendingUp, AlertTriangle, Plus } from "lucide-react";
import { formatCurrency, formatPercent } from "@/lib/utils";

const MOCK_PORTFOLIO = {
  name: "Main Portfolio",
  totalValue: 487250,
  dayChange: 3420,
  dayChangePct: 0.71,
  holdings: [
    { ticker: "NVDA", shares: 120, avgCost: 85.20, currentPrice: 114.30, weight: 28.1, gain: 34.15 },
    { ticker: "AAPL", shares: 200, avgCost: 155.00, currentPrice: 207.50, weight: 24.7, gain: 33.87 },
    { ticker: "MSFT", shares: 50, avgCost: 310.00, currentPrice: 417.20, weight: 18.2, gain: 34.58 },
    { ticker: "GOOGL", shares: 100, avgCost: 128.50, currentPrice: 172.10, weight: 14.5, gain: 33.93 },
    { ticker: "AMD", shares: 200, avgCost: 110.00, currentPrice: 142.00, weight: 8.5, gain: 29.09 },
    { ticker: "META", shares: 10, avgCost: 420.00, currentPrice: 549.00, weight: 6.0, gain: 30.71 },
  ],
  riskMetrics: {
    concentration: "High — top 3 = 71% of portfolio",
    sectorConcentration: "Very High — 100% Technology",
    maxDrawdownRisk: "Elevated due to high-beta growth exposure",
    correlationRisk: "High — all positions correlated to tech/AI narrative",
  },
};

export default function PortfolioPage() {
  const p = MOCK_PORTFOLIO;
  return (
    <div className="max-w-[1400px] space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Portfolio Intelligence</h1>
        <button className="px-3 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5">
          <Plus className="w-4 h-4" /> Add Holding
        </button>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs text-[var(--text-muted)] mb-1">Total Value</p>
          <p className="text-2xl font-bold">{formatCurrency(p.totalValue)}</p>
        </div>
        <div className="card">
          <p className="text-xs text-[var(--text-muted)] mb-1">Day Change</p>
          <p className={`text-2xl font-bold ${p.dayChange >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {p.dayChange >= 0 ? "+" : ""}{formatCurrency(p.dayChange)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-[var(--text-muted)] mb-1">Day Return</p>
          <p className={`text-2xl font-bold ${p.dayChangePct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {formatPercent(p.dayChangePct)}
          </p>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="card">
        <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Holdings</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[var(--text-muted)] text-xs uppercase tracking-wider">
              <th className="text-left py-2">Ticker</th>
              <th className="text-right py-2">Shares</th>
              <th className="text-right py-2">Avg Cost</th>
              <th className="text-right py-2">Current</th>
              <th className="text-right py-2">Weight</th>
              <th className="text-right py-2">Gain</th>
            </tr>
          </thead>
          <tbody>
            {p.holdings.map(h => (
              <tr key={h.ticker} className="border-t border-[var(--border)] hover:bg-white/[0.02]">
                <td className="py-2.5 font-semibold text-blue-400">{h.ticker}</td>
                <td className="text-right py-2.5">{h.shares}</td>
                <td className="text-right py-2.5">${h.avgCost.toFixed(2)}</td>
                <td className="text-right py-2.5">${h.currentPrice.toFixed(2)}</td>
                <td className="text-right py-2.5">{h.weight}%</td>
                <td className={`text-right py-2.5 font-medium ${h.gain >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {formatPercent(h.gain)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Risk Metrics */}
      <div className="card">
        <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Risk Analysis</h3>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(p.riskMetrics).map(([k, v]) => (
            <div key={k} className="flex items-start gap-2 p-3 bg-[var(--bg-elevated)] rounded-lg">
              <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-[var(--text-muted)] capitalize">{k.replace(/([A-Z])/g, " $1")}</p>
                <p className="text-sm text-[var(--text-secondary)] mt-0.5">{v}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
