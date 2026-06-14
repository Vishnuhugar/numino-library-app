'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, Search, Pencil, Trash2, BookOpen, X } from 'lucide-react';
import { booksApi, type Book } from '@/lib/api';
import { useUI } from '@/components/ui/UIProvider';

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
      const r = await booksApi.list({ page, size: SIZE, search: search?.trim() || undefined, available_only: avail });
      setBooks(r.items); setTotal(r.total);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }, [page, search, avail]);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => { setSelected(null); setModal('create'); };
  const openEdit   = (b: Book) => { setSelected(b); setModal('edit'); };

  const [deletingIds, setDeletingIds] = useState<string[]>([]);
  const { confirm, showToast } = useUI();

  const handleDelete = async (b: Book) => {
    const ok = await confirm({ title: 'Delete Book', message: `Delete "${b.title}"?` });
    if (!ok) return;
    setDeletingIds(ids => [...ids, b.id]);
    try { await booksApi.delete(b.id); load(); onAction(); }
    catch (e: any) { showToast(e.message || 'Delete failed'); }
    finally { setDeletingIds(ids => ids.filter(i => i !== b.id)); }
  };

  const pages = Math.max(1, Math.ceil(total / SIZE));

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="header-title">Books Catalogue</h1>
          <div className="header-sub">{total} title{total !== 1 ? 's' : ''} in the collection</div>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>
          <Plus size={16} /> Add Book
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="input-with-icon input-flex">
          <Search size={15} className="icon-left" />
          <input className="library-input with-pad input-small"
                 placeholder="Search title or author…"
                 value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <label className="filters-label">
          <input type="checkbox" checked={avail} onChange={e => { setAvail(e.target.checked); setPage(1); }} />
          Available only
        </label>
      </div>

      {error && <div className="error-msg">{error}</div>}
      {/* Table */}
      <div className="table-wrap">
        {loading ? (
          <div className="loading-empty">Loading…</div>
        ) : books.length === 0 ? (
          <div className="loading-empty">No books found.</div>
        ) : (
          <table className="lib-table">
            <thead>
              <tr>
                <th>Title</th><th>Author</th><th>Genre</th><th>ISBN</th>
                <th className="text-center">Copies</th><th className="text-center">Available</th>
                <th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {books.map(b => (
                <tr key={b.id}>
                  <td className="cell-strong">{b.title}</td>
                  <td className="cell-muted">{b.author}</td>
                  <td className="cell-small">{b.genre || '—'}</td>
                  <td className="cell-small mono">{b.isbn || '—'}</td>
                  <td className="text-center">{b.total_copies}</td>
                  <td className="text-center">{b.available_copies}</td>
                  <td>
                    <span className={`badge ${b.available_copies > 0 ? 'badge-available' : 'badge-unavail'}`}>
                      {b.available_copies > 0 ? 'Available' : 'Out'}
                    </span>
                  </td>
                  <td>
                    <div className="action-row">
                      <button className="btn btn-ghost btn-sm" onClick={() => openEdit(b)}><Pencil size={13}/></button>
                      <button className="btn btn-ghost btn-sm text-danger" onClick={() => handleDelete(b)}><Trash2 size={13}/></button>
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
        <div className="pagination">
          <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p-1)}>← Prev</button>
          <span className="small-muted">Page {page} of {pages}</span>
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
      {/* Using UIProvider confirm/toast - no local dialogs here */}
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
      title: form.title.trim(), author: form.author.trim(),
      isbn: form.isbn?.trim() || null, genre: form.genre?.trim() || null,
      publisher: form.publisher?.trim() || null,
      published_year: form.published_year ? Number(form.published_year) : null,
      total_copies: Number(form.total_copies),
      description: form.description?.trim() || null,
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
      <div className="modal-box modal-max-600" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{book ? 'Edit Book' : 'Add New Book'}</h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm"><X size={16}/></button>
        </div>
        <div className="modal-content">
          {error && <div className="modal-error">{error}</div>}
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
              <label className="form-label">{label}</label>
              <input className="library-input" value={(form as any)[key]} onChange={set(key)} />
            </div>
          ))}
          <div>
            <label className="form-label">Description</label>
            <textarea className="library-input" rows={3} value={form.description} onChange={set('description')} />
          </div>
        </div>
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving || !form.title.trim() || !form.author.trim()}>
            {saving ? 'Saving…' : book ? 'Save Changes' : 'Add Book'}
          </button>
        </div>
      </div>
    </div>
  );
}

