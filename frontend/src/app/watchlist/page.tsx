"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Eye, Plus, Trash2, TrendingUp, RefreshCw, X } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Watchlist {
  id: number;
  name: string;
  items: string[];
}

export default function WatchlistPage() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [newName, setNewName] = useState("");
  const [loading, setLoading] = useState(true);
  const [addingTicker, setAddingTicker] = useState<Record<number, string>>({});

  const fetchAllWatchlists = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API}/watchlists`);
      const list = await res.json();
      
      // Fetch details for each watchlist in parallel to get their actual tickers
      const detailed = await Promise.all(
        list.map(async (wl: any) => {
          const detailRes = await fetch(`${API}/watchlists/${wl.id}`);
          if (detailRes.ok) {
            return await detailRes.json();
          }
          return { id: wl.id, name: wl.name, items: [] };
        })
      );
      setWatchlists(detailed);
    } catch (err) {
      console.error("Failed to load watchlists:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllWatchlists();
  }, []);

  const addWatchlist = async () => {
    if (!newName.trim()) return;
    try {
      const res = await fetch(`${API}/watchlists`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName.trim() }),
      });
      if (res.ok) {
        const created = await res.json();
        setWatchlists(prev => [...prev, { id: created.id, name: created.name, items: [] }]);
        setNewName("");
      }
    } catch (err) {
      console.error("Failed to create watchlist:", err);
    }
  };

  const addTickerToWatchlist = async (watchlistId: number) => {
    const ticker = addingTicker[watchlistId]?.trim().toUpperCase();
    if (!ticker) return;

    try {
      const res = await fetch(`${API}/watchlists/${watchlistId}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker }),
      });
      if (res.ok) {
        setWatchlists(prev => prev.map(wl => {
          if (wl.id === watchlistId) {
            if (!wl.items.includes(ticker)) {
              return { ...wl, items: [...wl.items, ticker] };
            }
          }
          return wl;
        }));
        setAddingTicker(prev => ({ ...prev, [watchlistId]: "" }));
      }
    } catch (err) {
      console.error("Failed to add ticker:", err);
    }
  };

  const removeTickerFromWatchlist = async (watchlistId: number, ticker: string) => {
    try {
      const res = await fetch(`${API}/watchlists/${watchlistId}/items/${ticker}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setWatchlists(prev => prev.map(wl => {
          if (wl.id === watchlistId) {
            return { ...wl, items: wl.items.filter(t => t !== ticker) };
          }
          return wl;
        }));
      }
    } catch (err) {
      console.error("Failed to remove ticker:", err);
    }
  };

  return (
    <div className="max-w-[1400px] space-y-6 pb-12">
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Institutional Watchlists</h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Organize tracked investments into structured panels for continuous thesis monitoring.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            value={newName} 
            onChange={e => setNewName(e.target.value)}
            placeholder="New watchlist name..."
            className="bg-[var(--bg-elevated)] border border-[var(--border)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            onKeyDown={e => e.key === "Enter" && addWatchlist()}
          />
          <button onClick={addWatchlist} className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 rounded-lg text-xs font-semibold text-white transition-colors flex items-center gap-1.5">
            <Plus className="w-3.5 h-3.5" /> Create List
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-44 bg-slate-900 border border-[var(--border)] rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {watchlists.map(wl => (
            <div key={wl.id} className="card p-5 rounded-xl border border-[var(--border)] flex flex-col justify-between h-full bg-slate-900/20 hover:border-slate-800 transition-all">
              <div>
                <div className="flex items-center justify-between mb-4 border-b border-slate-950 pb-2">
                  <h3 className="font-bold text-base text-[var(--text-primary)]">{wl.name}</h3>
                  <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-[var(--text-muted)] font-black uppercase">
                    {wl.items.length} Tracked
                  </span>
                </div>

                <div className="flex flex-wrap gap-2 mb-6">
                  {wl.items.map(t => (
                    <div 
                      key={t} 
                      className="group flex items-center gap-1.5 bg-slate-950/60 border border-[var(--border)] hover:border-blue-500/30 px-2.5 py-1 rounded-lg text-xs transition-colors"
                    >
                      <Link href={`/research/${t}`} className="font-semibold text-blue-400 hover:text-blue-300">
                        {t}
                      </Link>
                      <button 
                        onClick={() => removeTickerFromWatchlist(wl.id, t)}
                        className="text-[var(--text-muted)] hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity ml-1"
                        title={`Remove ${t}`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                  {wl.items.length === 0 && (
                    <p className="text-xs text-[var(--text-muted)] italic py-2">No stocks tracked in this list.</p>
                  )}
                </div>
              </div>

              {/* Add ticker inline */}
              <div className="flex gap-2 pt-3 border-t border-slate-950 mt-auto">
                <input
                  value={addingTicker[wl.id] || ""}
                  onChange={e => setAddingTicker(prev => ({ ...prev, [wl.id]: e.target.value }))}
                  placeholder="e.g. NVDA"
                  className="bg-slate-950 border border-[var(--border)] rounded-md px-2 py-1 text-xs uppercase w-full focus:outline-none focus:border-blue-500/50"
                  onKeyDown={e => e.key === "Enter" && addTickerToWatchlist(wl.id)}
                />
                <button 
                  onClick={() => addTickerToWatchlist(wl.id)}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded-md text-xs font-semibold transition-colors flex-shrink-0"
                >
                  Add Ticker
                </button>
              </div>
            </div>
          ))}

          {watchlists.length === 0 && (
            <div className="col-span-full text-center py-12 border border-[var(--border)] border-dashed rounded-xl bg-slate-900/10">
              <p className="text-sm text-[var(--text-muted)]">No watchlists found. Use the input above to create your first watchlist.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
