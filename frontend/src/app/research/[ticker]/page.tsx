"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowUpRight, ArrowDownRight, AlertTriangle, Shield, TrendingUp, BarChart3, Brain, Target, Zap, Users, ChevronDown } from "lucide-react";
import { formatCurrency, formatPercent, formatNumber, severityColor } from "@/lib/utils";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, Radar } from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ResearchPage() {
  const params = useParams();
  const ticker = (params.ticker as string)?.toUpperCase();
  const [brain, setBrain] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    fetch(`${API}/companies/${ticker}/research`)
      .then(r => { if (!r.ok) throw new Error("Not found"); return r.json(); })
      .then(d => { setBrain(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [ticker]);

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorState ticker={ticker} message={error} />;
  if (!brain) return null;

  const { profile, key_metrics, valuation, peers, health_score, signals, scenarios, risks, ai_summary, ai_what_changed, ai_synthesis, price_history } = brain;

  return (
    <div className="max-w-[1400px] space-y-6">
      {/* 1. Company Header */}
      <CompanyHeader profile={profile} metrics={key_metrics} />
      {/* 2. Signal Stack */}
      <SignalStack signals={signals} />
      {/* 3. What Changed */}
      <WhatChanged text={ai_what_changed} />
      {/* 4. Market Expectations */}
      <MarketExpectations valuation={valuation} />
      {/* 5. Key Metrics */}
      <KeyMetrics metrics={key_metrics} prices={price_history} />
      {/* 6. Peer Comparison */}
      <PeerComparison peers={peers} />
      {/* 7. Scenarios */}
      <Scenarios scenarios={scenarios} price={key_metrics?.price} />
      {/* 8. Risks */}
      <Risks risks={risks} healthScore={health_score} />
      {/* 9. AI Synthesis */}
      <AISynthesis summary={ai_summary} synthesis={ai_synthesis} />
    </div>
  );
}

/* ─── Section Components ─────────────────────────── */

function CompanyHeader({ profile, metrics }: any) {
  return (
    <div className="card animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold">{profile.ticker}</h1>
            <span className="text-sm text-[var(--text-muted)] bg-[var(--bg-elevated)] px-2 py-0.5 rounded">{profile.exchange}</span>
          </div>
          <p className="text-[var(--text-secondary)]">{profile.name}</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">{profile.sector} · {profile.industry}</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold">${metrics?.price?.toFixed(2)}</p>
          <div className="flex items-center gap-4 mt-1 text-sm">
            <span className="text-[var(--text-muted)]">MCap {formatCurrency(metrics?.market_cap || 0, true)}</span>
            <span className="text-[var(--text-muted)]">EV {formatCurrency((metrics?.ev || 0) * 1e6, true)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function SignalStack({ signals }: any) {
  if (!signals?.length) return null;
  return (
    <section className="animate-fade-in-delay-1">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
        <Zap className="w-5 h-5 text-amber-400" /> Signal Stack
        <span className="text-xs text-[var(--text-muted)] ml-1">({signals.length})</span>
      </h2>
      <div className="space-y-2">
        {signals.map((s: any, i: number) => (
          <div key={i} className="card flex items-start gap-3 py-3">
            <span className={`severity-dot severity-${s.severity} mt-1.5`} />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className={`badge ${s.direction === "negative" ? "badge-negative" : s.direction === "positive" ? "badge-positive" : "badge-neutral"}`}>
                  {s.severity}
                </span>
                <span className="text-sm font-medium">{s.title}</span>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1">{s.explanation}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function WhatChanged({ text }: any) {
  return (
    <section className="card animate-fade-in-delay-1">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
        <AlertTriangle className="w-5 h-5 text-blue-400" /> What Changed
      </h2>
      <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{text}</p>
    </section>
  );
}

function MarketExpectations({ valuation }: any) {
  if (!valuation) return null;
  return (
    <section className="card animate-fade-in-delay-2">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
        <Target className="w-5 h-5 text-purple-400" /> Market Expectations (Reverse DCF)
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <MetricBox label="Implied Revenue CAGR" value={`${valuation.implied_revenue_cagr}%`} />
        <MetricBox label="WACC" value={`${valuation.assumptions?.wacc}%`} />
        <MetricBox label="Terminal Growth" value={`${valuation.assumptions?.terminal_growth}%`} />
        <MetricBox label="Current Op Margin" value={`${valuation.current_op_margin}%`} />
      </div>
      <p className="text-sm text-[var(--text-secondary)] italic bg-[var(--bg-elevated)] p-3 rounded-lg">
        💡 {valuation.interpretation}
      </p>
      {/* Sensitivity Table */}
      {valuation.sensitivity?.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <p className="text-xs text-[var(--text-muted)] mb-2 font-medium uppercase tracking-wider">Fair Value Sensitivity (WACC × Terminal Growth)</p>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[var(--text-muted)]">
                <th className="text-left py-1 px-2">WACC</th>
                {Object.keys(valuation.sensitivity[0]).filter((k: string) => k.startsWith("tg_")).map((k: string) => (
                  <th key={k} className="text-right py-1 px-2">TG {k.replace("tg_", "")}%</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {valuation.sensitivity.map((row: any, i: number) => (
                <tr key={i} className="border-t border-[var(--border)]">
                  <td className="py-1.5 px-2 font-medium">{row.wacc}%</td>
                  {Object.keys(row).filter((k: string) => k.startsWith("tg_")).map((k: string) => (
                    <td key={k} className="text-right py-1.5 px-2 font-mono">${row[k]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function KeyMetrics({ metrics, prices }: any) {
  const metricCards = [
    { label: "P/E Ratio", value: metrics?.pe_ratio ? `${metrics.pe_ratio}x` : "N/A" },
    { label: "EV/Revenue", value: metrics?.ev_revenue ? `${metrics.ev_revenue}x` : "N/A" },
    { label: "EV/EBITDA", value: metrics?.ev_ebitda ? `${metrics.ev_ebitda}x` : "N/A" },
    { label: "FCF Yield", value: metrics?.fcf_yield ? `${metrics.fcf_yield}%` : "N/A" },
    { label: "Revenue Growth", value: metrics?.revenue_growth ? formatPercent(metrics.revenue_growth) : "N/A" },
    { label: "Gross Margin", value: metrics?.gross_margin ? `${metrics.gross_margin}%` : "N/A" },
    { label: "Op Margin", value: metrics?.operating_margin ? `${metrics.operating_margin}%` : "N/A" },
    { label: "Debt/EBITDA", value: metrics?.debt_to_ebitda ? `${metrics.debt_to_ebitda}x` : "N/A" },
  ];

  return (
    <section className="animate-fade-in-delay-2">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
        <BarChart3 className="w-5 h-5 text-emerald-400" /> Key Metrics
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        {metricCards.map((m, i) => (
          <div key={i} className="card py-3">
            <p className="text-xs text-[var(--text-muted)] mb-1">{m.label}</p>
            <p className="text-lg font-semibold">{m.value}</p>
          </div>
        ))}
      </div>
      {/* Price Chart */}
      {prices?.length > 0 && (
        <div className="card" style={{ height: 200 }}>
          <ResponsiveContainer>
            <AreaChart data={prices}>
              <defs>
                <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={false} axisLine={false} />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} width={50} />
              <Tooltip contentStyle={{ background: "#1a1f2e", border: "1px solid #2a3142", borderRadius: 8, fontSize: 12 }} />
              <Area type="monotone" dataKey="close" stroke="#3b82f6" fill="url(#priceGrad)" strokeWidth={1.5} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}

function PeerComparison({ peers }: any) {
  if (!peers?.peers?.length) return null;
  const allCompanies = [peers.target, ...peers.peers];
  return (
    <section className="animate-fade-in-delay-2">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
        <Users className="w-5 h-5 text-blue-400" /> Peer Comparison
      </h2>
      <div className="card overflow-x-auto">
        {peers.signal && (
          <div className={`badge mb-3 ${peers.direction === "positive" ? "badge-positive" : peers.direction === "negative" ? "badge-negative" : "badge-neutral"}`}>
            {peers.signal}
          </div>
        )}
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[var(--text-muted)] text-xs uppercase tracking-wider">
              <th className="text-left py-2">Ticker</th>
              <th className="text-right py-2">EV/Rev</th>
              <th className="text-right py-2">EV/EBITDA</th>
              <th className="text-right py-2">P/E</th>
              <th className="text-right py-2">Rev Growth</th>
              <th className="text-right py-2">Op Margin</th>
            </tr>
          </thead>
          <tbody>
            {allCompanies.map((c: any, i: number) => (
              <tr key={i} className={`border-t border-[var(--border)] ${i === 0 ? "bg-blue-500/5" : ""}`}>
                <td className={`py-2 font-medium ${i === 0 ? "text-blue-400" : ""}`}>{c.ticker}{i === 0 ? " ★" : ""}</td>
                <td className="text-right py-2">{c.ev_revenue ? `${c.ev_revenue}x` : "—"}</td>
                <td className="text-right py-2">{c.ev_ebitda ? `${c.ev_ebitda}x` : "—"}</td>
                <td className="text-right py-2">{c.pe_ratio ? `${c.pe_ratio}x` : "—"}</td>
                <td className={`text-right py-2 ${c.revenue_growth >= 0 ? "text-emerald-400" : "text-red-400"}`}>{c.revenue_growth != null ? formatPercent(c.revenue_growth) : "—"}</td>
                <td className="text-right py-2">{c.operating_margin ? `${c.operating_margin}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {peers.medians && (
          <div className="mt-2 pt-2 border-t border-[var(--border)] flex gap-4 text-xs text-[var(--text-muted)]">
            <span>Peer Median: EV/Rev {peers.medians.ev_revenue}x</span>
            <span>EV/EBITDA {peers.medians.ev_ebitda}x</span>
            <span>P/E {peers.medians.pe_ratio}x</span>
          </div>
        )}
      </div>
    </section>
  );
}

function Scenarios({ scenarios, price }: any) {
  if (!scenarios) return null;
  const items = [
    { key: "bull", label: "Bull Case", color: "text-emerald-400", bg: "bg-emerald-500/10", icon: ArrowUpRight },
    { key: "base", label: "Base Case", color: "text-blue-400", bg: "bg-blue-500/10", icon: Target },
    { key: "bear", label: "Bear Case", color: "text-red-400", bg: "bg-red-500/10", icon: ArrowDownRight },
  ];
  return (
    <section className="animate-fade-in-delay-3">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
        <TrendingUp className="w-5 h-5 text-amber-400" /> Scenario Analysis
      </h2>
      <div className="grid grid-cols-3 gap-3">
        {items.map(({ key, label, color, bg, icon: Icon }) => {
          const sc = scenarios[key];
          const diff = price > 0 ? ((sc.price / price - 1) * 100) : 0;
          return (
            <div key={key} className="card">
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-7 h-7 rounded-lg ${bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${color}`} />
                </div>
                <span className={`text-sm font-semibold ${color}`}>{label}</span>
              </div>
              <p className="text-2xl font-bold">${sc.price?.toFixed(2)}</p>
              <p className={`text-sm font-medium ${diff >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {diff >= 0 ? "+" : ""}{diff.toFixed(1)}%
              </p>
              <p className="text-xs text-[var(--text-muted)] mt-2">{sc.thesis}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function Risks({ risks, healthScore }: any) {
  return (
    <section className="animate-fade-in-delay-3">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
        <Shield className="w-5 h-5 text-red-400" /> Risks & Health
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Risk Factors</h3>
          {risks?.length > 0 ? (
            <ul className="space-y-2">
              {risks.map((r: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
                  <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                  {r}
                </li>
              ))}
            </ul>
          ) : <p className="text-sm text-[var(--text-muted)]">No significant risk factors detected.</p>}
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Financial Health</h3>
          <div className="flex items-center gap-4 mb-3">
            <div className="w-16 h-16 rounded-full border-4 border-blue-500/30 flex items-center justify-center">
              <span className="text-xl font-bold">{healthScore?.grade}</span>
            </div>
            <div>
              <p className="text-lg font-semibold">{healthScore?.label}</p>
              <p className="text-sm text-[var(--text-muted)]">Score: {healthScore?.overall_score}/100</p>
            </div>
          </div>
          <div className="space-y-2">
            {healthScore?.sub_scores && Object.entries(healthScore.sub_scores).map(([k, v]: any) => (
              <div key={k} className="flex items-center gap-2">
                <span className="text-xs text-[var(--text-muted)] w-24 capitalize">{k.replace("_", " ")}</span>
                <div className="flex-1 h-2 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${v}%` }} />
                </div>
                <span className="text-xs font-medium w-8 text-right">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function AISynthesis({ summary, synthesis }: any) {
  return (
    <section className="card animate-fade-in-delay-3">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
        <Brain className="w-5 h-5 text-purple-400" /> AI Synthesis
      </h2>
      <div className="space-y-3">
        <div className="bg-[var(--bg-elevated)] p-4 rounded-lg">
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{summary}</p>
        </div>
        <div className="bg-[var(--bg-elevated)] p-4 rounded-lg">
          <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Deep Analysis</p>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{synthesis}</p>
        </div>
      </div>
    </section>
  );
}

function MetricBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[var(--bg-elevated)] p-3 rounded-lg">
      <p className="text-xs text-[var(--text-muted)] mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 max-w-[1400px]">
      <div className="skeleton h-24" />
      <div className="skeleton h-40" />
      <div className="grid grid-cols-4 gap-3">{[1,2,3,4].map(i=><div key={i} className="skeleton h-20"/>)}</div>
      <div className="skeleton h-48" />
    </div>
  );
}

function ErrorState({ ticker, message }: { ticker: string; message: string }) {
  return (
    <div className="flex items-center justify-center h-[50vh]">
      <div className="text-center">
        <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">No data for {ticker}</h2>
        <p className="text-[var(--text-muted)]">{message}</p>
        <p className="text-sm text-[var(--text-muted)] mt-2">Try: AAPL, MSFT, NVDA, GOOGL, AMZN, META, AMD, TSLA</p>
      </div>
    </div>
  );
}
