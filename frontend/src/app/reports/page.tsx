"use client";
import { FileText, Plus, Clock } from "lucide-react";

const MOCK_REPORTS = [
  { id: 1, ticker: "NVDA", type: "Stock Memo", title: "NVDA — AI Infrastructure Thesis", date: "2025-05-15" },
  { id: 2, ticker: "AAPL", type: "Bull/Bear", title: "AAPL — Bull vs Bear Analysis", date: "2025-05-12" },
  { id: 3, ticker: null, type: "Portfolio Risk", title: "Q2 2025 Portfolio Risk Review", date: "2025-05-10" },
];

export default function ReportsPage() {
  return (
    <div className="max-w-[1400px] space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Reports</h1>
        <button className="px-3 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5">
          <Plus className="w-4 h-4" /> Generate Report
        </button>
      </div>
      <div className="space-y-3">
        {MOCK_REPORTS.map(r => (
          <div key={r.id} className="card hover:border-blue-500/30 cursor-pointer">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-purple-400" />
                <div>
                  <p className="font-semibold">{r.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    {r.ticker && <span className="text-xs font-medium text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">{r.ticker}</span>}
                    <span className="text-xs text-[var(--text-muted)]">{r.type}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                <Clock className="w-3 h-3" /> {r.date}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
