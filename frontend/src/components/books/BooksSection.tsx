'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, Search, Pencil, Trash2, BookOpen, X } from 'lucide-react';
import { booksApi, type Book } from '@/lib/api';

export default function BooksSection({ onAction }: { onAction: () => void }) {
  const [books, setBooks]     = useState<Book[]>([]);
  const [total, setTotal]     = useState(0);
  const [page, setPage]       = useState(1);
  const [search, setSearch]   = useState('');
  const [avail, setAvail]     = useState(false);
  const [loading, setLoading] = useState(true);
  const [modal, setModal]     = useState<'create' | 'edit' | null>(null);
  const [selected, setSelected] = useState<Book | null>(null);
  const [error, setError]     = useState('');

  const SIZE = 10;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await booksApi.list({ page, size: SIZE, search: search || undefined, available_only: avail });
      setBooks(r.items); setTotal(r.total);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }, [page, search, avail]);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => { setSelected(null); setModal('create'); };
  const openEdit   = (b: Book) => { setSelected(b); setModal('edit'); };

  const handleDelete = async (b: Book) => {
    if (!confirm(`Delete "${b.title}"?`)) return;
    try { await booksApi.delete(b.id); load(); onAction(); }
    catch (e: any) { alert(e.message); }
  };

  const pages = Math.max(1, Math.ceil(total / SIZE));

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontFamily:"'Playfair Display',serif", fontSize:'1.8rem' }}>Books Catalogue</h1>
          <div style={{ color:'rgba(26,18,8,0.5)', fontFamily:"'Crimson Text',serif" }}>
            {total} title{total !== 1 ? 's' : ''} in the collection
          </div>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>
          <Plus size={16} /> Add Book
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div style={{ position:'relative', flex:1, maxWidth:360 }}>
          <Search size={15} style={{ position:'absolute', left:10, top:'50%', transform:'translateY(-50%)', color:'rgba(26,18,8,0.4)' }} />
          <input className="library-input" style={{ paddingLeft:32 }}
                 placeholder="Search title or author…"
                 value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <label style={{ display:'flex', alignItems:'center', gap:6, fontFamily:"'Crimson Text',serif", cursor:'pointer' }}>
          <input type="checkbox" checked={avail} onChange={e => { setAvail(e.target.checked); setPage(1); }} />
          Available only
        </label>
      </div>

      {error && <div style={{ color:'#8b1a1a', marginBottom:12 }}>{error}</div>}

      {/* Table */}
      <div style={{ background:'rgba(253,246,227,0.7)', border:'1px solid rgba(200,151,42,0.2)', borderRadius:2 }}>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'rgba(26,18,8,0.4)', fontFamily:"'Crimson Text',serif" }}>Loading…</div>
        ) : books.length === 0 ? (
          <div style={{ padding:40, textAlign:'center', color:'rgba(26,18,8,0.4)', fontFamily:"'Crimson Text',serif" }}>No books found.</div>
        ) : (
          <table className="lib-table">
            <thead>
              <tr>
                <th>Title</th><th>Author</th><th>Genre</th><th>ISBN</th>
                <th style={{ textAlign:'center' }}>Copies</th><th style={{ textAlign:'center' }}>Available</th>
                <th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {books.map(b => (
                <tr key={b.id}>
                  <td style={{ fontWeight:600 }}>{b.title}</td>
                  <td style={{ color:'rgba(26,18,8,0.7)' }}>{b.author}</td>
                  <td style={{ color:'rgba(26,18,8,0.6)', fontSize:'0.88rem' }}>{b.genre || '—'}</td>
                  <td style={{ fontFamily:"'Courier New',monospace", fontSize:'0.82rem', color:'rgba(26,18,8,0.5)' }}>{b.isbn || '—'}</td>
                  <td style={{ textAlign:'center' }}>{b.total_copies}</td>
                  <td style={{ textAlign:'center' }}>{b.available_copies}</td>
                  <td>
                    <span className={`badge ${b.available_copies > 0 ? 'badge-available' : 'badge-unavail'}`}>
                      {b.available_copies > 0 ? 'Available' : 'Out'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display:'flex', gap:8 }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => openEdit(b)}><Pencil size={13}/></button>
                      <button className="btn btn-ghost btn-sm" style={{ color:'#8b1a1a' }} onClick={() => handleDelete(b)}><Trash2 size={13}/></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div style={{ display:'flex', gap:8, marginTop:16, alignItems:'center' }}>
          <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p-1)}>← Prev</button>
          <span style={{ fontFamily:"'Crimson Text',serif", color:'rgba(26,18,8,0.6)' }}>
            Page {page} of {pages}
          </span>
          <button className="btn btn-ghost btn-sm" disabled={page === pages} onClick={() => setPage(p => p+1)}>Next →</button>
        </div>
      )}

      {modal && (
        <BookModal
          book={selected}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); load(); onAction(); }}
        />
      )}
    </div>
  );
}

// ── Book Modal ──────────────────────────────────────────────────────────────
function BookModal({ book, onClose, onSaved }: { book: Book | null; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({
    title: book?.title ?? '', author: book?.author ?? '', isbn: book?.isbn ?? '',
    genre: book?.genre ?? '', publisher: book?.publisher ?? '',
    published_year: book?.published_year ? String(book.published_year) : '',
    total_copies: book?.total_copies ? String(book.total_copies) : '1',
    description: book?.description ?? '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState('');

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async () => {
    setSaving(true); setError('');
    const payload: any = {
      title: form.title, author: form.author,
      isbn: form.isbn || null, genre: form.genre || null,
      publisher: form.publisher || null,
      published_year: form.published_year ? Number(form.published_year) : null,
      total_copies: Number(form.total_copies),
      description: form.description || null,
    };
    try {
      if (book) await booksApi.update(book.id, payload);
      else       await booksApi.create(payload);
      onSaved();
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div style={{ padding:'24px 28px', borderBottom:'1px solid rgba(200,151,42,0.2)', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
          <h2 style={{ fontFamily:"'Playfair Display',serif", fontSize:'1.3rem' }}>
            {book ? 'Edit Book' : 'Add New Book'}
          </h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm"><X size={16}/></button>
        </div>
        <div style={{ padding:'24px 28px', display:'flex', flexDirection:'column', gap:14 }}>
          {error && <div style={{ color:'#8b1a1a', fontFamily:"'Crimson Text',serif" }}>{error}</div>}
          {[
            { label:'Title *',       key:'title' },
            { label:'Author *',      key:'author' },
            { label:'ISBN',          key:'isbn' },
            { label:'Genre',         key:'genre' },
            { label:'Publisher',     key:'publisher' },
            { label:'Published Year',key:'published_year' },
            { label:'Total Copies',  key:'total_copies' },
          ].map(({ label, key }) => (
            <div key={key}>
              <label style={{ display:'block', fontFamily:"'Crimson Text',serif", fontWeight:600, marginBottom:4, fontSize:'0.9rem', color:'rgba(26,18,8,0.7)' }}>{label}</label>
              <input className="library-input" value={(form as any)[key]} onChange={set(key)} />
            </div>
          ))}
          <div>
            <label style={{ display:'block', fontFamily:"'Crimson Text',serif", fontWeight:600, marginBottom:4, fontSize:'0.9rem', color:'rgba(26,18,8,0.7)' }}>Description</label>
            <textarea className="library-input" rows={3} value={form.description} onChange={set('description')} />
          </div>
        </div>
        <div style={{ padding:'16px 28px', borderTop:'1px solid rgba(200,151,42,0.2)', display:'flex', gap:10, justifyContent:'flex-end' }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving || !form.title || !form.author}>
            {saving ? 'Saving…' : book ? 'Save Changes' : 'Add Book'}
          </button>
        </div>
      </div>
    </div>
  );
}
