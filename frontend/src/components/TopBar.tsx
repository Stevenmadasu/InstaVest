"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Bell } from "lucide-react";

export function TopBar() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/research/${query.trim().toUpperCase()}`);
      setQuery("");
    }
  };

  return (
    <header className="sticky top-0 z-40 h-14 bg-[var(--bg-primary)]/80 backdrop-blur-xl border-b border-[var(--border)] flex items-center justify-between px-6">
      <form onSubmit={handleSearch} className="flex-1 max-w-lg">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search ticker or company (e.g. AAPL, Microsoft)..."
            className="w-full bg-[var(--bg-card)] border border-[var(--border)] rounded-lg pl-10 pr-4 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/30 transition-all"
          />
        </div>
      </form>
      <div className="flex items-center gap-3 ml-4">
        <button className="relative p-2 rounded-lg hover:bg-white/[0.04] transition-colors">
          <Bell className="w-4 h-4 text-[var(--text-secondary)]" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-500 rounded-full" />
        </button>
      </div>
    </header>
  );
}
