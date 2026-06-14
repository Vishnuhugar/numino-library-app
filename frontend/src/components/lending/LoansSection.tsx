'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, RotateCcw, DollarSign, X, Search } from 'lucide-react';
import { loansApi, membersApi, booksApi, type Loan, type Member, type Book } from '@/lib/api';
import { useUI } from '@/components/ui/UIProvider';

export default function LoansSection({ onAction }: { onAction: () => void }) {
  const [loans, setLoans]     = useState<Loan[]>([]);
  const [total, setTotal]     = useState(0);
  const [page, setPage]       = useState(1);
  const [activeOnly, setActiveOnly] = useState(false);
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [modal, setModal]     = useState(false);
  const [error, setError]     = useState('');

  const SIZE = 10;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await loansApi.list({ page, size: SIZE, active_only: activeOnly, overdue_only: overdueOnly });
      setLoans(r.items); setTotal(r.total);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }, [page, activeOnly, overdueOnly]);

  useEffect(() => { load(); }, [load]);

  const [returningIds, setReturningIds] = useState<string[]>([]);
  const { showToast, confirm } = useUI();

  const doReturn = async (loan: Loan) => {
    setReturningIds(ids => [...ids, loan.id]);
    try { await loansApi.return(loan.id); load(); onAction(); }
    catch (e: any) { showToast(e.message || 'Failed to return'); }
    finally { setReturningIds(ids => ids.filter(i => i !== loan.id)); }
  };

  const handlePayFine = async (loan: Loan) => {
    try { await loansApi.payFine(loan.id); load(); onAction(); }
    catch (e: any) { showToast(e.message || 'Failed to process fine'); }
  };

  const pages = Math.max(1, Math.ceil(total / SIZE));
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="header-title">Loans & Lending</h1>
          <div className="header-sub">{total} loan record{total !== 1 ? 's' : ''}</div>
        </div>
        <button className="btn btn-primary" onClick={() => setModal(true)}>
          <Plus size={16}/> New Loan
        </button>
      </div>

      <div className="flex gap-4 mb-6">
        <label className="filters-label">
          <input type="checkbox" checked={activeOnly} onChange={e => { setActiveOnly(e.target.checked); setOverdueOnly(false); setPage(1); }} />
          Active only
        </label>
        <label className="filters-label">
          <input type="checkbox" checked={overdueOnly} onChange={e => { setOverdueOnly(e.target.checked); setActiveOnly(false); setPage(1); }} />
          Overdue only
        </label>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <div className="table-wrap">
        {loading ? (
          <div className="loading-empty">Loading…</div>
        ) : loans.length === 0 ? (
          <div className="loading-empty">No loans found.</div>
        ) : (
          <table className="lib-table">
            <thead>
              <tr>
                <th>Book</th><th>Member</th><th>Borrowed</th>
                <th>Due Date</th><th>Returned</th><th>Fine</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {loans.map(loan => {
                const isOverdue = !loan.returned_at && loan.due_date < today;
                const isActive  = !loan.returned_at;
                const fine      = Number(loan.fine_amount);
                return (
                  <tr key={loan.id}>
                    <td>
                      <div className="cell-strong">{loan.book_title}</div>
                      <div className="cell-sub">{loan.book_author}</div>
                    </td>
                    <td style={{ color:'rgba(26,18,8,0.7)' }}>{loan.member_name}</td>
                    <td style={{ fontSize:'0.88rem', color:'rgba(26,18,8,0.55)' }}>
                      {new Date(loan.borrowed_at).toLocaleDateString()}
                    </td>
                    <td style={{ fontSize:'0.88rem', color: isOverdue ? '#8b1a1a' : 'rgba(26,18,8,0.55)', fontWeight: isOverdue ? 600 : 400 }}>
                      {new Date(loan.due_date).toLocaleDateString()}
                    </td>
                    <td className="cell-small">{loan.returned_at ? new Date(loan.returned_at).toLocaleDateString() : '—'}</td>
                    <td>
                      {fine > 0 ? (
                        <span style={{ color: loan.fine_paid ? '#2d5016' : '#8b1a1a', fontWeight:600 }}>
                          ${fine.toFixed(2)} {loan.fine_paid ? '✓' : ''}
                        </span>
                      ) : '—'}
                    </td>
                    <td>
                      <span className={`badge ${isActive ? (isOverdue ? 'badge-overdue' : 'badge-active') : 'badge-returned'}`}>
                        {isActive ? (isOverdue ? 'Overdue' : 'Active') : 'Returned'}
                      </span>
                    </td>
                    <td>
                      <div className="action-row">
                        {isActive && (
                          <button className="btn btn-ghost btn-sm" title="Return book" onClick={async () => {
                            const ok = await confirm({ title: 'Return Book', message: `Return "${loan.book_title}"?` });
                            if (!ok) return;
                            await doReturn(loan);
                          }}>
                            <RotateCcw size={13}/>
                          </button>
                        )}
                        {!isActive && fine > 0 && !loan.fine_paid && (
                          <button className="btn btn-ghost btn-sm payfine-btn" title="Pay fine" onClick={() => handlePayFine(loan)}>
                            <DollarSign size={13}/>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {pages > 1 && (
        <div className="pagination">
          <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p-1)}>← Prev</button>
          <span className="small-muted">Page {page} of {pages}</span>
          <button className="btn btn-ghost btn-sm" disabled={page === pages} onClick={() => setPage(p => p+1)}>Next →</button>
        </div>
      )}

      {modal && (
        <BorrowModal
          onClose={() => setModal(false)}
          onSaved={() => { setModal(false); load(); onAction(); }}
        />
      )}
    </div>
  );
}

// ── Borrow Modal ─────────────────────────────────────────────────────────────
function BorrowModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [members, setMembers] = useState<Member[]>([]);
  const [books,   setBooks]   = useState<Book[]>([]);
  const [memberId, setMemberId] = useState('');
  const [bookId,   setBookId]   = useState('');
  const [notes, setNotes]       = useState('');
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState('');
  const [memberSearch, setMemberSearch] = useState('');
  const [bookSearch, setBookSearch]     = useState('');

  useEffect(() => {
    membersApi.list({ size: 100, active_only: true }).then(r => setMembers(r.items)).catch(() => {});
    booksApi.list({ size: 100, available_only: true }).then(r => setBooks(r.items)).catch(() => {});
  }, []);

  const filteredMembers = members.filter(m =>
    !memberSearch || m.name.toLowerCase().includes(memberSearch.toLowerCase()) || m.email.toLowerCase().includes(memberSearch.toLowerCase())
  );
  const filteredBooks = books.filter(b =>
    !bookSearch || b.title.toLowerCase().includes(bookSearch.toLowerCase()) || b.author.toLowerCase().includes(bookSearch.toLowerCase())
  );

  const selClass = (selected: boolean) => selected ? 'list-item selected' : 'list-item';

  const handleSubmit = async () => {
    if (!memberId || !bookId) { setError('Please select a member and a book.'); return; }
    setSaving(true); setError('');
    try {
      await loansApi.borrow({ member_id: memberId, book_id: bookId, notes: notes || undefined });
      onSaved();
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box modal-max-600" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title modal-title-lg">Record New Loan</h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm"><X size={16}/></button>
        </div>

        <div className="modal-content-grid">
          {/* Member picker */}
          <div>
            <label className="form-label">Select Member *</label>
            <div className="input-with-icon mb-8">
              <Search size={13} className="icon-left" />
              <input className="library-input with-pad input-small" placeholder="Search members…" value={memberSearch} onChange={e => setMemberSearch(e.target.value)} />
            </div>
            <div className="list-box">
              {filteredMembers.length === 0 ? (
                <div className="list-empty">No active members</div>
              ) : filteredMembers.map(m => (
                <div key={m.id} className={selClass(memberId === m.id)} onClick={() => setMemberId(m.id)}>
                  <div className="list-item-title">{m.name}</div>
                  <div className="list-item-sub">{m.email}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Book picker */}
          <div>
            <label className="form-label">Select Book *</label>
            <div className="input-with-icon mb-8">
              <Search size={13} className="icon-left" />
              <input className="library-input with-pad input-small" placeholder="Search available books…" value={bookSearch} onChange={e => setBookSearch(e.target.value)} />
            </div>
            <div className="list-box">
              {filteredBooks.length === 0 ? (
                <div className="list-empty">No available books</div>
              ) : filteredBooks.map(b => (
                <div key={b.id} className={selClass(bookId === b.id)} onClick={() => setBookId(b.id)}>
                  <div className="list-item-title">{b.title}</div>
                  <div className="list-item-sub">{b.author} · {b.available_copies} avail.</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="modal-content">
          <label className="form-label">Notes</label>
          <textarea className="library-input" rows={2} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Optional notes…"/>
        </div>

        {error && <div className="modal-error">{error}</div>}

        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving || !memberId || !bookId}>
            {saving ? 'Recording…' : 'Record Loan'}
          </button>
        </div>
      </div>
    </div>
  );
}
