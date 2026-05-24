"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Search, Briefcase, Target, TrendingUp, FileText, Activity, Database } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
  { href: "/explore", label: "Explore", icon: Search },
  { href: "/watchlist", label: "Watchlist", icon: TrendingUp },
  { href: "/thesis", label: "Thesis Boards", icon: Target },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/signals", label: "Signals", icon: Activity },
  { href: "/reports", label: "Reports", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[240px] bg-[var(--bg-secondary)] border-r border-[var(--border)] flex flex-col z-50">
      {/* Logo */}
      <div className="p-5 border-b border-[var(--border)]">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="text-base font-bold text-[var(--text-primary)] tracking-tight">InstaVest</span>
            <span className="block text-[10px] text-[var(--text-muted)] uppercase tracking-widest">Signal Terminal</span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-3">
        <div className="space-y-0.5">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150
                  ${isActive
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.04]"
                  }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : ""}`} />
                {label}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[var(--border)]">
        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          <Database className="w-3 h-3" />
          <span>Mock Data Active</span>
        </div>
      </div>
    </aside>
  );
}
