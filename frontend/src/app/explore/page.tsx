"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, TrendingUp, Filter } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExplorePage() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/companies/trending`)
      .then(r => r.json())
      .then(d => { setCompanies(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const handleSearch = (q: string) => {
    setSearch(q);
    if (q.length > 0) {
      fetch(`${API}/companies/search?q=${q}`)
        .then(r => r.json())
        .then(setCompanies)
        .catch(() => {});
    } else {
      fetch(`${API}/companies/trending`).then(r => r.json()).then(setCompanies);
    }
  };

  return (
    <div className="max-w-[1400px] space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Explore Stocks</h1>
      </div>
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
        <input
          type="text" value={search} onChange={e => handleSearch(e.target.value)}
          placeholder="Filter by ticker or name..."
          className="w-full bg-[var(--bg-card)] border border-[var(--border)] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-blue-500/50"
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {companies.map((c: any) => (
          <Link key={c.ticker} href={`/research/${c.ticker}`} className="card group hover:border-blue-500/30 cursor-pointer">
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg font-bold">{c.ticker}</span>
              {c.price && <span className="text-lg font-semibold">${c.price?.toFixed(2)}</span>}
            </div>
            <p className="text-sm text-[var(--text-secondary)]">{c.name}</p>
            <div className="flex items-center justify-between mt-3 text-xs text-[var(--text-muted)]">
              <span>{c.sector}</span>
              {c.market_cap && <span>{formatCurrency(c.market_cap, true)}</span>}
            </div>
          </Link>
        ))}
      </div>
      {companies.length === 0 && !loading && (
        <div className="text-center py-20 text-[var(--text-muted)]">
          <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>No companies found. Try AAPL, MSFT, NVDA, GOOGL.</p>
        </div>
      )}
    </div>
  );
}
