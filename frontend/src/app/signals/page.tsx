"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, Zap } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SignalsPage() {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const fetchSignals = async () => {
    try {
      setLoading(true);
      // Fetch from the direct high-performance SQL signals route
      const res = await fetch(`${API}/signals`);
      if (res.ok) {
        const d = await res.json();
        setSignals(d || []);
      }
    } catch (err) {
      console.error("Failed to fetch signals:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, []);

  const filtered = filter === "all" ? signals : signals.filter((s: any) => s.direction === filter);

  return (
    <div className="max-w-[1400px] space-y-6 pb-12">
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2 text-[var(--text-primary)]">
            <Activity className="w-6 h-6 text-amber-400" /> Priority Signal Feed
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Real-time, SQL-prioritized anomaly feed tracking structural changes across tracked equities.
          </p>
        </div>
        <div className="flex gap-2">
          {["all", "negative", "positive"].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all capitalize border ${
                filter === f 
                  ? "bg-blue-500/10 text-blue-400 border-blue-500/30" 
                  : "bg-slate-900 text-[var(--text-muted)] border-[var(--border)] hover:text-white hover:border-slate-800"
              }`}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-slate-900 border border-[var(--border)] rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((s: any, i: number) => {
            const isNeg = s.direction === "negative";
            return (
              <Link 
                key={i} 
                href={`/research/${s.ticker}`} 
                className="card flex items-start gap-4 p-4 hover:border-blue-500/20 bg-slate-900/10 hover:bg-slate-900/30 transition-all border border-[var(--border)] rounded-xl group"
              >
                <span className={`w-2.5 h-2.5 rounded-full mt-2 flex-shrink-0 ${
                  s.severity === "high" ? "bg-red-400 animate-pulse" : s.severity === "medium" ? "bg-amber-400" : "bg-blue-400"
                }`} />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <span className="text-[10px] font-black text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded tracking-wider uppercase">
                      {s.ticker}
                    </span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                      s.severity === "high" 
                        ? "bg-red-500/10 text-red-400 border border-red-500/25" 
                        : "bg-amber-500/10 text-amber-400 border border-amber-500/25"
                    }`}>
                      {s.severity} severity
                    </span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                      isNeg ? "bg-red-500/10 text-red-400" : "bg-emerald-500/10 text-emerald-400"
                    }`}>
                      {s.direction}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-[var(--text-primary)]">{s.title}</p>
                  <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">{s.explanation}</p>
                </div>
                <div className="text-right flex-shrink-0 font-mono text-[10px] font-bold bg-slate-950 px-2.5 py-1 rounded text-[var(--text-muted)] mt-1">
                  Score: {s.priority_score}
                </div>
              </Link>
            );
          })}

          {filtered.length === 0 && (
            <div className="text-center py-20 border border-[var(--border)] border-dashed rounded-xl bg-slate-900/10">
              <Zap className="w-12 h-12 mx-auto mb-4 opacity-30 text-[var(--text-muted)]" />
              <p className="text-sm text-[var(--text-muted)]">No active signals found matching current filter.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
