'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, RotateCcw, DollarSign, X, Search } from 'lucide-react';
import { loansApi, membersApi, booksApi, type Loan, type Member, type Book } from '@/lib/api';

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

  const handleReturn = async (loan: Loan) => {
    if (!confirm(`Return "${loan.book_title}"?`)) return;
    try { await loansApi.return(loan.id); load(); onAction(); }
    catch (e: any) { alert(e.message); }
  };

  const handlePayFine = async (loan: Loan) => {
    try { await loansApi.payFine(loan.id); load(); onAction(); }
    catch (e: any) { alert(e.message); }
  };

  const pages = Math.max(1, Math.ceil(total / SIZE));
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontFamily:"'Playfair Display',serif", fontSize:'1.8rem' }}>Loans & Lending</h1>
          <div style={{ color:'rgba(26,18,8,0.5)', fontFamily:"'Crimson Text',serif" }}>
            {total} loan record{total !== 1 ? 's' : ''}
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => setModal(true)}>
          <Plus size={16}/> New Loan
        </button>
      </div>

      <div className="flex gap-4 mb-6">
        <label style={{ display:'flex', alignItems:'center', gap:6, fontFamily:"'Crimson Text',serif", cursor:'pointer' }}>
          <input type="checkbox" checked={activeOnly} onChange={e => { setActiveOnly(e.target.checked); setOverdueOnly(false); setPage(1); }} />
          Active only
        </label>
        <label style={{ display:'flex', alignItems:'center', gap:6, fontFamily:"'Crimson Text',serif", cursor:'pointer' }}>
          <input type="checkbox" checked={overdueOnly} onChange={e => { setOverdueOnly(e.target.checked); setActiveOnly(false); setPage(1); }} />
          Overdue only
        </label>
      </div>

      {error && <div style={{ color:'#8b1a1a', marginBottom:12 }}>{error}</div>}

      <div style={{ background:'rgba(253,246,227,0.7)', border:'1px solid rgba(200,151,42,0.2)', borderRadius:2 }}>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'rgba(26,18,8,0.4)', fontFamily:"'Crimson Text',serif" }}>Loading…</div>
        ) : loans.length === 0 ? (
          <div style={{ padding:40, textAlign:'center', color:'rgba(26,18,8,0.4)', fontFamily:"'Crimson Text',serif" }}>No loans found.</div>
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
                      <div style={{ fontWeight:600, fontSize:'0.95rem' }}>{loan.book_title}</div>
                      <div style={{ color:'rgba(26,18,8,0.5)', fontSize:'0.82rem' }}>{loan.book_author}</div>
                    </td>
                    <td style={{ color:'rgba(26,18,8,0.7)' }}>{loan.member_name}</td>
                    <td style={{ fontSize:'0.88rem', color:'rgba(26,18,8,0.55)' }}>
                      {new Date(loan.borrowed_at).toLocaleDateString()}
                    </td>
                    <td style={{ fontSize:'0.88rem', color: isOverdue ? '#8b1a1a' : 'rgba(26,18,8,0.55)', fontWeight: isOverdue ? 600 : 400 }}>
                      {new Date(loan.due_date).toLocaleDateString()}
                    </td>
                    <td style={{ fontSize:'0.88rem', color:'rgba(26,18,8,0.55)' }}>
                      {loan.returned_at ? new Date(loan.returned_at).toLocaleDateString() : '—'}
                    </td>
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
                      <div style={{ display:'flex', gap:6 }}>
                        {isActive && (
                          <button className="btn btn-ghost btn-sm" title="Return book" onClick={() => handleReturn(loan)}>
                            <RotateCcw size={13}/>
                          </button>
                        )}
                        {!isActive && fine > 0 && !loan.fine_paid && (
                          <button className="btn btn-ghost btn-sm" title="Pay fine" style={{ color:'#c8972a' }} onClick={() => handlePayFine(loan)}>
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
        <div style={{ display:'flex', gap:8, marginTop:16, alignItems:'center' }}>
          <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p-1)}>← Prev</button>
          <span style={{ fontFamily:"'Crimson Text',serif", color:'rgba(26,18,8,0.6)' }}>Page {page} of {pages}</span>
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

  const handleSubmit = async () => {
    if (!memberId || !bookId) { setError('Please select a member and a book.'); return; }
    setSaving(true); setError('');
    try {
      await loansApi.borrow({ member_id: memberId, book_id: bookId, notes: notes || undefined });
      onSaved();
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  const selStyle = (selected: boolean): React.CSSProperties => ({
    padding:'10px 14px', cursor:'pointer', borderRadius:2, marginBottom:2,
    background: selected ? 'rgba(200,151,42,0.15)' : 'transparent',
    borderLeft: selected ? '3px solid #c8972a' : '3px solid transparent',
    fontFamily:"'Crimson Text',serif",
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" style={{ maxWidth:600 }} onClick={e => e.stopPropagation()}>
        <div style={{ padding:'24px 28px', borderBottom:'1px solid rgba(200,151,42,0.2)', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
          <h2 style={{ fontFamily:"'Playfair Display',serif", fontSize:'1.3rem' }}>Record New Loan</h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm"><X size={16}/></button>
        </div>

        <div style={{ padding:'20px 28px', display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
          {/* Member picker */}
          <div>
            <label style={{ display:'block', fontFamily:"'Crimson Text',serif", fontWeight:600, marginBottom:6, fontSize:'0.9rem', color:'rgba(26,18,8,0.7)' }}>
              Select Member *
            </label>
            <div style={{ position:'relative', marginBottom:8 }}>
              <Search size={13} style={{ position:'absolute', left:9, top:'50%', transform:'translateY(-50%)', color:'rgba(26,18,8,0.4)' }}/>
              <input className="library-input" style={{ paddingLeft:28, fontSize:'0.88rem' }} placeholder="Search members…" value={memberSearch} onChange={e => setMemberSearch(e.target.value)} />
            </div>
            <div style={{ maxHeight:200, overflowY:'auto', border:'1px solid rgba(200,151,42,0.2)', borderRadius:2 }}>
              {filteredMembers.length === 0 ? (
                <div style={{ padding:12, color:'rgba(26,18,8,0.4)', fontFamily:"'Crimson Text',serif", fontSize:'0.9rem' }}>No active members</div>
              ) : filteredMembers.map(m => (
                <div key={m.id} style={selStyle(memberId === m.id)} onClick={() => setMemberId(m.id)}>
                  <div style={{ fontWeight:600, fontSize:'0.92rem' }}>{m.name}</div>
                  <div style={{ fontSize:'0.8rem', color:'rgba(26,18,8,0.55)' }}>{m.email}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Book picker */}
          <div>
            <label style={{ display:'block', fontFamily:"'Crimson Text',serif", fontWeight:600, marginBottom:6, fontSize:'0.9rem', color:'rgba(26,18,8,0.7)' }}>
              Select Book *
            </label>
            <div style={{ position:'relative', marginBottom:8 }}>
              <Search size={13} style={{ position:'absolute', left:9, top:'50%', transform:'translateY(-50%)', color:'rgba(26,18,8,0.4)' }}/>
              <input className="library-input" style={{ paddingLeft:28, fontSize:'0.88rem' }} placeholder="Search available books…" value={bookSearch} onChange={e => setBookSearch(e.target.value)} />
            </div>
            <div style={{ maxHeight:200, overflowY:'auto', border:'1px solid rgba(200,151,42,0.2)', borderRadius:2 }}>
              {filteredBooks.length === 0 ? (
                <div style={{ padding:12, color:'rgba(26,18,8,0.4)', fontFamily:"'Crimson Text',serif", fontSize:'0.9rem' }}>No available books</div>
              ) : filteredBooks.map(b => (
                <div key={b.id} style={selStyle(bookId === b.id)} onClick={() => setBookId(b.id)}>
                  <div style={{ fontWeight:600, fontSize:'0.92rem' }}>{b.title}</div>
                  <div style={{ fontSize:'0.8rem', color:'rgba(26,18,8,0.55)' }}>{b.author} · {b.available_copies} avail.</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ padding:'0 28px 20px' }}>
          <label style={{ display:'block', fontFamily:"'Crimson Text',serif", fontWeight:600, marginBottom:4, fontSize:'0.9rem', color:'rgba(26,18,8,0.7)' }}>Notes</label>
          <textarea className="library-input" rows={2} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Optional notes…"/>
        </div>

        {error && <div style={{ padding:'0 28px 16px', color:'#8b1a1a', fontFamily:"'Crimson Text',serif" }}>{error}</div>}

        <div style={{ padding:'16px 28px', borderTop:'1px solid rgba(200,151,42,0.2)', display:'flex', gap:10, justifyContent:'flex-end' }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving || !memberId || !bookId}>
            {saving ? 'Recording…' : 'Record Loan'}
          </button>
        </div>
      </div>
    </div>
  );
}
