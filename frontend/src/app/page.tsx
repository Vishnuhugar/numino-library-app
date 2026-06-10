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
  <aside
    style={{ width: 240, background: '#1a1208', flexShrink: 0 }}
    className="flex flex-col py-8 px-4"
  >
    {/* Logo */}
    <div className="mb-8 px-2">
      <div
        className="text-2xl font-bold mb-0.5"
        style={{
          fontFamily: "'Playfair Display', serif",
          color: '#c8972a',
        }}
      >
        📚 LibraryOS
      </div>

      <div
        style={{
          color: 'rgba(253,246,227,0.45)',
          fontSize: '0.78rem',
          fontFamily: "'Crimson Text', serif",
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
        }}
      >
        Neighborhood Library
      </div>
    </div>

    {/* Ornament */}
    <div
      style={{
        height: 1,
        background: 'rgba(200,151,42,0.3)',
        margin: '0 8px 24px',
      }}
    />

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
    <div
      style={{
        color: 'rgba(253,246,227,0.3)',
        fontSize: '0.7rem',
        fontFamily: "'Crimson Text', serif",
        textAlign: 'center',
        marginTop: 24,
      }}
    >
      v1.0 · Library Management
    </div>
  </aside>

  {/* ── Main Content ─────────────────────────────────────── */}
  <main
    className="flex-1 overflow-auto"
    style={{ background: '#fdf6e3' }}
  >
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
          <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: '2rem', color: '#1a1208' }}>
            Library Dashboard
          </h1>
          <div style={{ color: 'rgba(26,18,8,0.5)', fontFamily: "'Crimson Text', serif" }}>
            An overview of library operations
          </div>
        </div>
        <button onClick={onRefresh} className="btn btn-ghost btn-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Ornamental rule */}
      <div className="ornamental-rule mb-8">
        <span style={{ fontFamily: "'Playfair Display', serif", color: '#c8972a', fontSize: '1.1rem' }}>
          ✦
        </span>
      </div>

      {/* Stat cards */}
      {loading ? (
        <div style={{ color: 'rgba(26,18,8,0.45)', fontFamily: "'Crimson Text', serif", fontSize: '1.05rem' }}>
          Loading statistics…
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6 mb-10" style={{ maxWidth: 700 }}>
          {cards.map(c => (
            <div key={c.label} className="stat-card">
              <div style={{ fontSize: '2rem', marginBottom: 4 }}>{c.icon}</div>
              <div style={{ fontSize: '2.4rem', fontFamily: "'Playfair Display', serif",
                            color: c.color, fontWeight: 700, lineHeight: 1 }}>
                {c.value}
              </div>
              <div style={{ color: 'rgba(26,18,8,0.55)', fontFamily: "'Crimson Text', serif",
                            fontSize: '0.95rem', marginTop: 4 }}>
                {c.label}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Overdue alert */}
      {stats && stats.overdue_loans > 0 && (
        <div style={{ background: 'rgba(139,26,26,0.07)', border: '1px solid rgba(139,26,26,0.3)',
                      borderRadius: 2, padding: '16px 20px', maxWidth: 700,
                      display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <AlertTriangle size={20} style={{ color: '#8b1a1a', flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontFamily: "'Playfair Display', serif", color: '#8b1a1a', fontWeight: 600 }}>
              Overdue Items
            </div>
            <div style={{ fontFamily: "'Crimson Text', serif", color: 'rgba(26,18,8,0.7)', fontSize: '0.95rem' }}>
              {stats.overdue_loans} loan{stats.overdue_loans > 1 ? 's are' : ' is'} past due.
              Outstanding fines: <strong>${Number(stats.total_fines).toFixed(2)}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Quick-start callouts */}
      <div className="ornamental-rule my-8" style={{ maxWidth: 700 }}>
        <span style={{ fontFamily: "'Playfair Display', serif", color: '#c8972a' }}>Quick Actions</span>
      </div>
      <div style={{ color: 'rgba(26,18,8,0.6)', fontFamily: "'Crimson Text', serif", maxWidth: 700 }}>
        Use the sidebar to navigate between <em>Books</em>, <em>Members</em>, and <em>Loans</em>.
        All lending operations — borrowing, returning, and fine payments — are managed under <em>Loans</em>.
      </div>
    </div>
  );
}
