'use client';

import { useState, useEffect, useCallback } from 'react';
import { BookOpen, Users, BookMarked, BarChart3, AlertTriangle, RefreshCw } from 'lucide-react';
import { loansApi, type LibraryStats } from '@/lib/api';
import BooksSection from '@/components/books/BooksSection';
import MembersSection from '@/components/members/MembersSection';
import LoansSection from '@/components/lending/LoansSection';

type Section = 'dashboard' | 'books' | 'members' | 'loans';

export default function Home() {
  const [section, setSection] = useState<Section>('dashboard');
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      setStats(await loansApi.stats());
    } catch (e) {
      console.error(e);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  const navItems: { key: Section; label: string; icon: React.ReactNode }[] = [
    { key: 'dashboard', label: 'Dashboard',  icon: <BarChart3 size={18} /> },
    { key: 'books',     label: 'Books',      icon: <BookOpen size={18} /> },
    { key: 'members',   label: 'Members',    icon: <Users size={18} /> },
    { key: 'loans',     label: 'Loans',      icon: <BookMarked size={18} /> },
  ];

  return (
    <div className="flex min-h-screen">
  {/* ── Sidebar ─────────────────────────────────────────── */}
  <aside className="sidebar flex flex-col py-8 px-4">
    {/* Logo */}
    <div className="mb-8 px-2">
      <div className="text-2xl font-bold mb-0.5 brand">📚 LibraryOS</div>
      <div className="brand-sub">Neighborhood Library</div>
    </div>

    {/* Ornament */}
    <div className="separator" />

    {/* Nav */}
    <nav className="flex flex-col gap-1 flex-1">
      {navItems.map(({ key, label, icon }) => (
        <button
          key={key}
          onClick={() => setSection(key)}
          className={`nav-item ${section === key ? 'active' : ''}`}
        >
          {icon}
          <span>{label}</span>
        </button>
      ))}
    </nav>

    {/* Footer */}
    <div className="sidebar-footer">v1.0 · Library Management</div>
  </aside>

  {/* ── Main Content ─────────────────────────────────────── */}
  <main className="flex-1 overflow-auto">
    {section === 'dashboard' && (
      <Dashboard
        stats={stats}
        loading={statsLoading}
        onRefresh={loadStats}
      />
    )}

    {section === 'books' && (
      <BooksSection onAction={loadStats} />
    )}

    {section === 'members' && (
      <MembersSection onAction={loadStats} />
    )}

    {section === 'loans' && (
      <LoansSection onAction={loadStats} />
    )}
  </main>
</div>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function Dashboard({ stats, loading, onRefresh }: {
  stats: LibraryStats | null; loading: boolean; onRefresh: () => void;
}) {
  const cards = stats ? [
    { label: 'Total Books',    value: stats.total_books,    icon: '📚', color: '#2d5016' },
    { label: 'Members',        value: stats.total_members,  icon: '👥', color: '#c8972a' },
    { label: 'Active Loans',   value: stats.active_loans,   icon: '📖', color: '#c8972a' },
    { label: 'Overdue Loans',  value: stats.overdue_loans,  icon: '⚠️', color: '#8b1a1a' },
  ] : [];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="page-title">Library Dashboard</h1>
          <div className="page-sub">An overview of library operations</div>
        </div>
        <button onClick={onRefresh} className="btn btn-ghost btn-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Ornamental rule */}
      <div className="ornamental-rule mb-8">
        <span className="ornament-icon">✦</span>
      </div>

      {/* Stat cards */}
      {loading ? (
        <div className="small-muted">Loading statistics…</div>
      ) : (
        <div className="grid grid-cols-2 gap-6 mb-10 constrain-700">
          {cards.map(c => (
            <div key={c.label} className="stat-card">
              <div className="stat-icon">{c.icon}</div>
              <div className={`stat-value ${c.color === '#2d5016' ? 'sv-green' : c.color === '#c8972a' ? 'sv-gold' : 'sv-red'}`}>
                {c.value}
              </div>
              <div className="small-muted mt-4">{c.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Overdue alert */}
      {stats && stats.overdue_loans > 0 && (
        <div className="overdue-alert">
          <AlertTriangle size={20} className="alert-icon" />
          <div>
            <div className="alert-title">Overdue Items</div>
            <div className="alert-body">
              {stats.overdue_loans} loan{stats.overdue_loans > 1 ? 's are' : ' is'} past due.
              Outstanding fines: <strong>${Number(stats.total_fines).toFixed(2)}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Quick-start callouts */}
      <div className="ornamental-rule my-8 constrain-700">
        <span className="ornament-icon">Quick Actions</span>
      </div>
      <div className="small-muted constrain-700">
        Use the sidebar to navigate between <em>Books</em>, <em>Members</em>, and <em>Loans</em>.
        All lending operations — borrowing, returning, and fine payments — are managed under <em>Loans</em>.
      </div>
    </div>
  );
}
