"use client";
import { useEffect, useState } from "react";
import { Target, Plus, Shield, AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp, Link as LinkIcon, HelpCircle } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Assumption {
  id: number;
  text: string;
  status: string;
  metric: string;
  ticker?: string;
  operator: string;
  threshold_value: number | null;
  current_value: number | null;
}

interface TimelineEvent {
  id: number;
  event_type: string;
  title: string;
  ticker: string;
  summary: string;
  what_changed: string;
  why_it_matters: string;
  created_at: string;
}

interface ThesisBoard {
  id: number;
  title: string;
  description: string;
  status: string;
  confidence: number;
  time_horizon: string;
  stocks: string[];
  assumptions: Assumption[];
  timeline: TimelineEvent[];
}

const STATUS_COLORS: Record<string, string> = {
  strengthening: "badge-positive",
  stable: "badge-neutral",
  weakening: "badge-warning",
  broken: "badge-negative",
};

const ASSUMPTION_ICONS: Record<string, any> = {
  active: { icon: Shield, color: "text-blue-400" },
  at_risk: { icon: AlertTriangle, color: "text-amber-400" },
  validated: { icon: CheckCircle, color: "text-emerald-400" },
  broken: { icon: XCircle, color: "text-red-400" },
};

export default function ThesisPage() {
  const [boards, setBoards] = useState<ThesisBoard[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // New Thesis state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newHorizon, setNewHorizon] = useState("medium");

  // New Ticker / Assumption state
  const [linkingTicker, setLinkingTicker] = useState<Record<number, string>>({});
  const [addingAsmText, setAddingAsmText] = useState<Record<number, string>>({});
  const [addingAsmMetric, setAddingAsmMetric] = useState<Record<number, string>>({});
  const [addingAsmOperator, setAddingAsmOperator] = useState<Record<number, string>>({});
  const [addingAsmThreshold, setAddingAsmThreshold] = useState<Record<number, string>>({});

  const fetchAllBoards = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API}/thesis`);
      const list = await res.json();
      
      // Parallel fetch board details
      const detailed = await Promise.all(
        list.map(async (b: any) => {
          const detailRes = await fetch(`${API}/thesis/${b.id}`);
          if (detailRes.ok) {
            return await detailRes.json();
          }
          return {
            ...b,
            description: "",
            time_horizon: "medium",
            assumptions: [],
            timeline: []
          };
        })
      );
      setBoards(detailed);
      if (detailed.length > 0 && expanded === null) {
        setExpanded(detailed[0].id);
      }
    } catch (err) {
      console.error("Failed to fetch thesis boards:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllBoards();
  }, []);

  const createBoard = async () => {
    if (!newTitle.trim()) return;
    try {
      const res = await fetch(`${API}/thesis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTitle.trim(),
          description: newDesc.trim(),
          time_horizon: newHorizon
        }),
      });
      if (res.ok) {
        setShowCreateModal(false);
        setNewTitle("");
        setNewDesc("");
        setNewHorizon("medium");
        fetchAllBoards();
      }
    } catch (err) {
      console.error("Failed to create board:", err);
    }
  };

  const linkStock = async (boardId: number) => {
    const ticker = linkingTicker[boardId]?.trim().toUpperCase();
    if (!ticker) return;
    try {
      const res = await fetch(`${API}/thesis/${boardId}/stocks?ticker=${ticker}`, {
        method: "POST"
      });
      if (res.ok) {
        setLinkingTicker(prev => ({ ...prev, [boardId]: "" }));
        // Refresh this single board details
        const detailRes = await fetch(`${API}/thesis/${boardId}`);
        if (detailRes.ok) {
          const updatedBoard = await detailRes.json();
          setBoards(prev => prev.map(b => b.id === boardId ? updatedBoard : b));
        }
      }
    } catch (err) {
      console.error("Failed to link stock:", err);
    }
  };

  const addAssumption = async (boardId: number) => {
    const text = addingAsmText[boardId]?.trim();
    const metric = addingAsmMetric[boardId] || "operating_margin";
    const op = addingAsmOperator[boardId] || ">=";
    const threshVal = parseFloat(addingAsmThreshold[boardId] || "0");

    if (!text) return;

    try {
      const res = await fetch(`${API}/thesis/${boardId}/assumptions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assumption_text: text,
          linked_metric: metric,
          operator: op,
          threshold_value: threshVal
        })
      });
      if (res.ok) {
        setAddingAsmText(prev => ({ ...prev, [boardId]: "" }));
        setAddingAsmThreshold(prev => ({ ...prev, [boardId]: "" }));
        // Refresh this single board details
        const detailRes = await fetch(`${API}/thesis/${boardId}`);
        if (detailRes.ok) {
          const updatedBoard = await detailRes.json();
          setBoards(prev => prev.map(b => b.id === boardId ? updatedBoard : b));
        }
      }
    } catch (err) {
      console.error("Failed to add assumption:", err);
    }
  };

  return (
    <div className="max-w-[1400px] space-y-6 pb-12">
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Institutional Thesis Boards</h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Track structural growth vectors, automatically validate operating metrics, and audit conviction.
          </p>
        </div>
        <button 
          onClick={() => setShowCreateModal(true)} 
          className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 rounded-lg text-xs font-semibold text-white transition-colors flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> New Thesis Board
        </button>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="card max-w-md w-full p-6 space-y-4 border border-[var(--border)] shadow-2xl bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-950 pb-2">
              <h2 className="text-base font-bold text-white">Create New Thesis Board</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-[var(--text-muted)] hover:text-white text-xs">Close</button>
            </div>
            
            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-[var(--text-secondary)] font-bold">Thesis Title</label>
                <input 
                  value={newTitle} 
                  onChange={e => setNewTitle(e.target.value)} 
                  placeholder="e.g. Hyperscaler capex growth acceleration"
                  className="w-full bg-slate-950 border border-[var(--border)] rounded px-3 py-2 text-white focus:outline-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[var(--text-secondary)] font-bold">Description</label>
                <textarea 
                  value={newDesc} 
                  onChange={e => setNewDesc(e.target.value)} 
                  placeholder="Why is this a structural investment paradigm?"
                  rows={3}
                  className="w-full bg-slate-950 border border-[var(--border)] rounded px-3 py-2 text-white focus:outline-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[var(--text-secondary)] font-bold">Horizon</label>
                <select 
                  value={newHorizon} 
                  onChange={e => setNewHorizon(e.target.value)}
                  className="w-full bg-slate-950 border border-[var(--border)] rounded px-3 py-2 text-white focus:outline-none"
                >
                  <option value="short">Short Term (1-12 months)</option>
                  <option value="medium">Medium Term (1-3 years)</option>
                  <option value="long">Long Term (3-5+ years)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 text-xs">
              <button onClick={() => setShowCreateModal(false)} className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded font-semibold text-white">Cancel</button>
              <button onClick={createBoard} className="px-3 py-2 bg-blue-500 hover:bg-blue-600 rounded font-semibold text-white">Create Board</button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2].map(i => (
            <div key={i} className="h-28 bg-slate-900 border border-[var(--border)] rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {boards.map(board => {
            const isOpen = expanded === board.id;
            return (
              <div key={board.id} className="card p-5 rounded-xl border border-[var(--border)] bg-slate-900/20 hover:border-slate-800 transition-all flex flex-col">
                <div 
                  className="cursor-pointer flex items-center justify-between" 
                  onClick={() => setExpanded(isOpen ? null : board.id)}
                >
                  <div className="flex items-center gap-3">
                    <Target className="w-5 h-5 text-indigo-400" />
                    <div>
                      <h3 className="text-base font-bold text-[var(--text-primary)]">{board.title}</h3>
                      <p className="text-xs text-[var(--text-muted)] mt-0.5">{board.description || "No description provided."}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className={`badge text-[10px] uppercase font-black tracking-wider ${STATUS_COLORS[board.status] || "badge-neutral"}`}>
                      {board.status}
                    </span>
                    <div className="text-right hidden sm:block">
                      <p className="text-xs font-semibold">Conviction: {board.confidence}%</p>
                      <div className="w-24 h-1.5 bg-slate-950 rounded-full mt-1">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${board.confidence}%` }} />
                      </div>
                    </div>
                    {isOpen ? <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" /> : <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />}
                  </div>
                </div>

                <div className="flex flex-wrap gap-1.5 mt-3 border-t border-slate-950 pt-2.5">
                  {board.stocks.map(t => (
                    <span key={t} className="text-[10px] font-black text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded tracking-wider uppercase border border-blue-500/10">
                      ${t}
                    </span>
                  ))}
                  {board.stocks.length === 0 && (
                    <span className="text-[10px] text-[var(--text-muted)] italic">No stocks linked.</span>
                  )}
                </div>

                {isOpen && (
                  <div className="mt-6 pt-6 border-t border-slate-950 space-y-6 animate-fade-in">
                    
                    {/* Assumptions Panel */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-black uppercase text-[var(--text-secondary)] tracking-widest">
                        Automated Metric Validations
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {board.assumptions.map(a => {
                          const statusKey = a.status === "validated" ? "validated" : a.status === "at_risk" ? "at_risk" : a.status === "broken" ? "broken" : "active";
                          const { icon: Icon, color } = ASSUMPTION_ICONS[statusKey];
                          return (
                            <div key={a.id} className="flex items-center gap-3 p-3 bg-slate-950/40 border border-[var(--border)] rounded-lg text-xs justify-between">
                              <div className="flex items-start gap-2.5">
                                <Icon className={`w-4 h-4 ${color} flex-shrink-0 mt-0.5`} />
                                <div className="space-y-0.5">
                                  <p className="font-semibold text-white leading-relaxed">{a.text}</p>
                                  <p className="text-[10px] text-[var(--text-muted)]">
                                    Linked Ticker: <span className="font-bold text-[var(--text-secondary)]">${a.ticker || board.stocks[0]}</span> | Metric: <span className="font-bold text-[var(--text-secondary)]">{a.metric}</span>
                                  </p>
                                </div>
                              </div>
                              <div className="text-right flex-shrink-0 ml-2">
                                <span className={`badge text-[9px] uppercase font-bold ${STATUS_COLORS[a.status] || "badge-neutral"}`}>{a.status}</span>
                                {a.current_value !== null && a.threshold_value !== null && (
                                  <p className="text-[9px] text-[var(--text-muted)] mt-1 font-semibold">
                                    {a.current_value} vs {a.operator} {a.threshold_value}
                                  </p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                        {board.assumptions.length === 0 && (
                          <div className="col-span-full py-4 text-center italic text-xs text-[var(--text-muted)]">
                            No assumptions set for this board. Add an assumption below to enable automated validation.
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Inline Link Stock & Add Assumption forms */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-950">
                      {/* Link a stock */}
                      <div className="space-y-2 text-xs">
                        <span className="font-bold text-[var(--text-secondary)] block">Link Stock Ticker</span>
                        <div className="flex gap-2">
                          <input 
                            value={linkingTicker[board.id] || ""}
                            onChange={e => setLinkingTicker(prev => ({ ...prev, [board.id]: e.target.value }))}
                            placeholder="e.g. MSFT"
                            className="bg-slate-950 border border-[var(--border)] rounded px-2.5 py-1.5 w-full uppercase"
                            onKeyDown={e => e.key === "Enter" && linkStock(board.id)}
                          />
                          <button 
                            onClick={() => linkStock(board.id)}
                            className="px-3 bg-slate-800 hover:bg-slate-700 text-white rounded font-semibold transition-colors"
                          >
                            Link
                          </button>
                        </div>
                      </div>

                      {/* Add assumption */}
                      <div className="space-y-3 text-xs">
                        <span className="font-bold text-[var(--text-secondary)] block">Add Assumption & Verification Rule</span>
                        <input 
                          value={addingAsmText[board.id] || ""}
                          onChange={e => setAddingAsmText(prev => ({ ...prev, [board.id]: e.target.value }))}
                          placeholder="Assumption: Gross margin stays above 40%"
                          className="w-full bg-slate-950 border border-[var(--border)] rounded px-2.5 py-1.5"
                        />
                        <div className="flex gap-2">
                          <select 
                            value={addingAsmMetric[board.id] || "operating_margin"}
                            onChange={e => setAddingAsmMetric(prev => ({ ...prev, [board.id]: e.target.value }))}
                            className="bg-slate-950 border border-[var(--border)] rounded px-2.5 py-1.5 w-full"
                          >
                            <option value="revenue_growth">Revenue Growth</option>
                            <option value="operating_margin">Operating Margin</option>
                            <option value="gross_margin">Gross Margin</option>
                            <option value="fcf_yield">Free Cash Flow Yield</option>
                            <option value="debt_to_ebitda">Debt to EBITDA</option>
                          </select>
                          <select 
                            value={addingAsmOperator[board.id] || ">="}
                            onChange={e => setAddingAsmOperator(prev => ({ ...prev, [board.id]: e.target.value }))}
                            className="bg-slate-950 border border-[var(--border)] rounded px-2.5 py-1.5"
                          >
                            <option value=">=">&gt;=</option>
                            <option value="<=">&lt;=</option>
                            <option value="==">==</option>
                          </select>
                          <input 
                            value={addingAsmThreshold[board.id] || ""}
                            onChange={e => setAddingAsmThreshold(prev => ({ ...prev, [board.id]: e.target.value }))}
                            placeholder="Val"
                            type="number"
                            step="0.01"
                            className="bg-slate-950 border border-[var(--border)] rounded px-2.5 py-1.5 w-20"
                          />
                          <button 
                            onClick={() => addAssumption(board.id)}
                            className="px-4 bg-blue-500 hover:bg-blue-600 text-white rounded font-bold transition-colors"
                          >
                            Add
                          </button>
                        </div>
                      </div>
                    </div>

                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
