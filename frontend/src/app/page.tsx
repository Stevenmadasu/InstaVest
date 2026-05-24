"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  ArrowRight,
  Zap,
  Globe,
  Shield,
  Clock,
  ChevronRight,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Radio,
  BarChart3,
  Brain,
  Layers,
  CheckSquare,
  Square,
} from "lucide-react";
import { initFirebase } from "@/lib/firebase";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ─── Types ──────────────────────────────────────── */
interface StreamItem {
  id: number;
  timestamp: string;
  severity: string;
  direction: string;
  evolution_type: string;
  entity_type: string;
  entity_id: string;
  narrative: string;
  prior_state: string | null;
  why_it_matters: string | null;
  implication: string | null;
  affected_tickers: string[];
  acceleration_score: number;
  importance_score: number;
  priority_score: number;
}

/* ─── Helpers ────────────────────────────────────── */
function timeAgo(isoDate: string): string {
  const now = new Date();
  const date = new Date(isoDate);
  const diffMs = now.getTime() - date.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function severityConfig(severity: string) {
  const map: Record<string, { color: string; bg: string; border: string; glow: string; icon: any }> = {
    critical: { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/30", glow: "shadow-red-500/10", icon: AlertTriangle },
    high: { color: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/30", glow: "shadow-orange-500/10", icon: TrendingDown },
    medium: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", glow: "shadow-amber-500/10", icon: Activity },
    positive: { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", glow: "shadow-emerald-500/10", icon: TrendingUp },
    low: { color: "text-slate-400", bg: "bg-slate-500/10", border: "border-slate-500/30", glow: "shadow-slate-500/5", icon: Minus },
  };
  return map[severity] || map.low;
}

function evolutionLabel(type: string): string {
  const map: Record<string, string> = {
    accelerating: "ACCELERATING",
    weakening: "WEAKENING",
    strengthening: "STRENGTHENING",
    reversing: "REVERSAL",
    diverging: "DIVERGING",
    stabilizing: "STABILIZING",
    deteriorating: "DETERIORATING",
    improving: "IMPROVING",
  };
  return map[type] || type.toUpperCase();
}

function entityIcon(type: string) {
  const map: Record<string, any> = {
    thesis: Brain,
    portfolio: Layers,
    ticker: BarChart3,
    signal: Radio,
    macro: Globe,
  };
  return map[type] || Activity;
}

/* ─── Components ─────────────────────────────────── */

function MacroBanner({ regime }: { regime: any }) {
  if (!regime) return null;
  return (
    <div className="macro-banner">
      <div className="macro-banner-inner">
        <div className="flex items-center gap-3">
          <Globe className="w-4 h-4 text-blue-400 shrink-0" />
          <span className="text-xs font-semibold tracking-widest uppercase text-blue-300">
            Macro Regime
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-slate-200">{regime.label || regime.regime}</span>
          <span className="text-xs text-slate-500">{Math.round((regime.confidence || 0) * 100)}% confidence</span>
        </div>
      </div>
    </div>
  );
}

function StreamCard({ item, index }: { item: StreamItem; index: number }) {
  const config = severityConfig(item.severity);
  const IconComponent = config.icon;
  const EntityIcon = entityIcon(item.entity_type);

  return (
    <div
      className={`stream-card ${config.border} ${config.glow}`}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Top bar: severity indicator + meta */}
      <div className="stream-card-header">
        <div className="flex items-center gap-2.5">
          <div className={`stream-severity-dot ${config.bg}`}>
            <IconComponent className={`w-3.5 h-3.5 ${config.color}`} />
          </div>
          <span className={`stream-evolution-badge ${config.bg} ${config.color}`}>
            {evolutionLabel(item.evolution_type)}
          </span>
          <span className="stream-entity-badge">
            <EntityIcon className="w-3 h-3" />
            {item.entity_type}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {item.affected_tickers.length > 0 && (
            <div className="flex gap-1.5">
              {item.affected_tickers.map((t) => (
                <Link
                  key={t}
                  href={`/research/${t}`}
                  className="stream-ticker-pill"
                >
                  {t}
                </Link>
              ))}
            </div>
          )}
          <span className="stream-timestamp">
            <Clock className="w-3 h-3" />
            {timeAgo(item.timestamp)}
          </span>
        </div>
      </div>

      {/* Core narrative */}
      <p className="stream-narrative">{item.narrative}</p>

      {/* Why it matters + implication */}
      {(item.why_it_matters || item.implication) && (
        <div className="stream-context">
          {item.why_it_matters && (
            <div className="stream-context-row">
              <span className="stream-context-label">Why it matters</span>
              <p className="stream-context-text">{item.why_it_matters}</p>
            </div>
          )}
          {item.implication && (
            <div className="stream-context-row">
              <span className="stream-context-label">Implication</span>
              <p className="stream-context-text">{item.implication}</p>
            </div>
          )}
        </div>
      )}

      {/* Bottom metrics bar */}
      <div className="stream-metrics">
        <div className="stream-metric">
          <Zap className="w-3 h-3 text-amber-400" />
          <span>Acceleration {(item.acceleration_score * 100).toFixed(0)}%</span>
        </div>
        <div className="stream-metric">
          <Shield className="w-3 h-3 text-blue-400" />
          <span>Priority {(item.priority_score * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}

function ThesisConvictionPanel({ boards }: { boards: any[] }) {
  if (!boards || boards.length === 0) return null;
  return (
    <div className="sidebar-panel">
      <div className="sidebar-panel-header">
        <Brain className="w-4 h-4 text-violet-400" />
        <span>Monitored Conviction</span>
      </div>
      <div className="sidebar-panel-body">
        {boards.map((b: any) => {
          const statusColor =
            b.status === "strengthening" ? "text-emerald-400" :
            b.status === "weakening" ? "text-amber-400" :
            b.status === "broken" ? "text-red-400" : "text-slate-400";
          return (
            <div key={b.id} className="conviction-row">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-200 truncate">{b.title}</p>
                <p className={`text-xs ${statusColor} capitalize`}>{b.status}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-sm font-semibold text-slate-100">{Math.round(b.confidence)}%</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ChecklistPanel({ items, onToggle }: { items: any[]; onToggle: (id: number, checked: boolean) => void }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="sidebar-panel">
      <div className="sidebar-panel-header">
        <CheckSquare className="w-4 h-4 text-blue-400" />
        <span>Action Checklist</span>
      </div>
      <div className="sidebar-panel-body">
        {items.map((item: any) => (
          <button
            key={item.id}
            onClick={() => onToggle(item.id, item.completed)}
            className="checklist-row"
          >
            {item.completed ? (
              <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <Square className="w-4 h-4 text-slate-500 shrink-0" />
            )}
            <span className={`text-xs ${item.completed ? "text-slate-500 line-through" : "text-slate-300"}`}>
              {item.message}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ─── Main Page ──────────────────────────────────── */
export default function IntelligenceStreamPage() {
  const [stream, setStream] = useState<StreamItem[]>([]);
  const [briefing, setBriefing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const [checkedActions, setCheckedActions] = useState<Record<number, boolean>>({});

  const loadData = useCallback(async () => {
    try {
      const [streamRes, briefingRes] = await Promise.all([
        fetch(`${API}/api/temporal/stream?limit=30&hours=168`).then(r => r.json()),
        fetch(`${API}/dashboard/morning-briefing`).then(r => r.json()),
      ]);
      setStream(streamRes.stream || []);
      setBriefing(briefingRes);
      const initialChecked: Record<number, boolean> = {};
      briefingRes.action_checklist?.forEach((item: any) => {
        initialChecked[item.id] = item.completed;
      });
      setCheckedActions(initialChecked);
    } catch (err) {
      console.error("Failed to load intelligence data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    initFirebase();
    loadData();
  }, [loadData]);

  const triggerPipeline = async () => {
    setPipelineRunning(true);
    setPipelineResult(null);
    try {
      const res = await fetch(`${API}/api/temporal/pipeline/trigger`, { method: "POST" });
      const result = await res.json();
      setPipelineResult(result);
      // Reload data after pipeline completes
      await loadData();
    } catch (err) {
      console.error("Pipeline trigger failed:", err);
      setPipelineResult({ errors: ["Failed to trigger pipeline"] });
    } finally {
      setPipelineRunning(false);
    }
  };

  const toggleAction = (itemId: number, isCurrentlyChecked: boolean) => {
    setCheckedActions(prev => ({ ...prev, [itemId]: !isCurrentlyChecked }));
    fetch(`${API}/dashboard/checklist/${itemId}/toggle`, { method: "POST" }).catch(() => {
      setCheckedActions(prev => ({ ...prev, [itemId]: isCurrentlyChecked }));
    });
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-pulse" />
        <p className="text-sm text-slate-500 mt-4">Compiling intelligence stream...</p>
      </div>
    );
  }

  const regime = briefing?.macro_regime;
  const boards = briefing?.thesis_conviction?.boards || [];
  const checklist = (briefing?.action_checklist || []).map((item: any) => ({
    ...item,
    completed: checkedActions[item.id] ?? item.completed,
  }));
  const featured = briefing?.featured_intelligence;

  return (
    <div className="intelligence-page">
      {/* ─── Header ──────────────────────────────── */}
      <header className="intelligence-header">
        <div className="intelligence-header-left">
          <div className="flex items-center gap-3">
            <div className="header-logo-mark">
              <Zap className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">InstaVest</h1>
              <p className="text-[10px] font-medium text-slate-500 uppercase tracking-[0.2em]">Investment Intelligence OS</p>
            </div>
          </div>
        </div>
        <nav className="intelligence-nav">
          <Link href="/" className="nav-link active">Stream</Link>
          <Link href="/thesis" className="nav-link">Thesis</Link>
          <Link href="/watchlist" className="nav-link">Watchlist</Link>
          <Link href="/portfolio" className="nav-link">Portfolio</Link>
          <Link href="/signals" className="nav-link">Signals</Link>
          <Link href="/explore" className="nav-link">Research</Link>
        </nav>
        <div className="intelligence-header-right">
          <button
            onClick={triggerPipeline}
            disabled={pipelineRunning}
            className="pipeline-trigger-btn"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${pipelineRunning ? "animate-spin" : ""}`} />
            {pipelineRunning ? "Running..." : "Run Pipeline"}
          </button>
        </div>
      </header>

      {/* ─── Macro Banner ────────────────────────── */}
      <MacroBanner regime={regime} />

      {/* ─── Pipeline Result Toast ───────────────── */}
      {pipelineResult && (
        <div className={`pipeline-toast ${pipelineResult.total_errors === 0 ? "pipeline-toast-success" : "pipeline-toast-warning"}`}>
          <div className="flex items-center gap-2">
            {pipelineResult.total_errors === 0 ? (
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            )}
            <span className="text-xs font-medium">
              Pipeline completed in {pipelineResult.pipeline_duration_seconds?.toFixed(1)}s
              {pipelineResult.total_errors > 0 && ` — ${pipelineResult.total_errors} error(s)`}
            </span>
          </div>
          <button onClick={() => setPipelineResult(null)} className="text-xs text-slate-500 hover:text-slate-300">
            Dismiss
          </button>
        </div>
      )}

      {/* ─── Main Content ────────────────────────── */}
      <div className="intelligence-layout">
        {/* Left: Intelligence Stream */}
        <main className="intelligence-stream">
          <div className="stream-section-header">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-blue-400" />
              <h2 className="text-sm font-semibold text-slate-200 tracking-wide uppercase">Intelligence Stream</h2>
            </div>
            <span className="text-xs text-slate-500">
              {stream.length} event{stream.length !== 1 ? "s" : ""} tracked
            </span>
          </div>

          {/* Featured Intelligence summary */}
          {featured && (
            <div className="featured-intelligence">
              <div className="featured-intelligence-header">
                <span className="text-[10px] font-semibold tracking-widest uppercase text-blue-400">Featured Analysis</span>
                <Link href={`/research/${featured.ticker}`} className="featured-ticker-link">
                  {featured.ticker}
                  <ArrowUpRight className="w-3 h-3" />
                </Link>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed mt-2">
                {featured.summary}
              </p>
              {featured.why_it_matters && (
                <p className="text-xs text-slate-500 leading-relaxed mt-1.5 italic">
                  {featured.why_it_matters}
                </p>
              )}
            </div>
          )}

          {/* Stream Items */}
          {stream.length === 0 ? (
            <div className="stream-empty">
              <Radio className="w-8 h-8 text-slate-600" />
              <p className="text-sm text-slate-500 mt-3">No intelligence events yet.</p>
              <p className="text-xs text-slate-600 mt-1">
                Trigger the pipeline to generate your first temporal intelligence stream.
              </p>
              <button onClick={triggerPipeline} disabled={pipelineRunning} className="pipeline-trigger-btn mt-4">
                <RefreshCw className={`w-3.5 h-3.5 ${pipelineRunning ? "animate-spin" : ""}`} />
                Run Pipeline
              </button>
            </div>
          ) : (
            <div className="stream-list">
              {stream.map((item, i) => (
                <StreamCard key={item.id} item={item} index={i} />
              ))}
            </div>
          )}
        </main>

        {/* Right: Sidebar */}
        <aside className="intelligence-sidebar">
          <ThesisConvictionPanel boards={boards} />
          <ChecklistPanel
            items={checklist}
            onToggle={toggleAction}
          />

          {/* Quick Links */}
          <div className="sidebar-panel">
            <div className="sidebar-panel-header">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Quick Navigation</span>
            </div>
            <div className="sidebar-panel-body">
              {[
                { href: "/thesis", label: "Thesis Boards", icon: Brain },
                { href: "/watchlist", label: "Watchlists", icon: BarChart3 },
                { href: "/portfolio", label: "Portfolio", icon: Layers },
                { href: "/signals", label: "Signal Feed", icon: Radio },
              ].map(({ href, label, icon: Icon }) => (
                <Link key={href} href={href} className="quick-nav-link">
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-3.5 h-3.5 text-slate-500" />
                    <span>{label}</span>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
                </Link>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
