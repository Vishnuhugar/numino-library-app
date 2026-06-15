'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, Search, Pencil, Trash2, X, UserCheck, UserX } from 'lucide-react';
import { membersApi, type Member } from '@/lib/api';
import { useUI } from '@/components/ui/UIProvider';
import DataTable from '@/components/ui/DataTable';
import ModalForm from '@/components/ui/ModalForm';

export default function MembersSection({ onAction }: { onAction: () => void }) {
  const [members, setMembers] = useState<Member[]>([]);
  const [total, setTotal]     = useState(0);
  const [page, setPage]       = useState(1);
  const [search, setSearch]   = useState('');
  const [activeOnly, setActiveOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [modal, setModal]     = useState<'create' | 'edit' | null>(null);
  const [selected, setSelected] = useState<Member | null>(null);
  const [error, setError]     = useState('');

  const SIZE = 10;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await membersApi.list({ page, size: SIZE, search: search?.trim() || undefined, active_only: activeOnly });
      setMembers(r.items); setTotal(r.total);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }, [page, search, activeOnly]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (m: Member) => {
    const ok = await confirm({ title: 'Remove Member', message: `Remove member "${m.name}"?` });
    if (!ok) return;
    await doDelete(m);
  };

  const handleToggleActive = async (m: Member) => {
    try { await membersApi.update(m.id, { is_active: !m.is_active }); load(); }
    catch (e: any) { showToast(e.message || 'Update failed'); }
  };

  const [deletingIds, setDeletingIds] = useState<string[]>([]);
  const { confirm, showToast } = useUI();
  const doDelete = async (m: Member) => {
    setDeletingIds(ids => [...ids, m.id]);
    try { await membersApi.delete(m.id); load(); onAction(); }
    catch (e: any) { showToast(e.message || 'Delete failed'); }
    finally { setDeletingIds(ids => ids.filter(i => i !== m.id)); }
  };

  const pages = Math.max(1, Math.ceil(total / SIZE));

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="header-title">Members</h1>
          <div className="header-sub">{total} registered member{total !== 1 ? 's' : ''}</div>
        </div>
        <button className="btn btn-primary" onClick={() => { setSelected(null); setModal('create'); }}>
          <Plus size={16}/> Add Member
        </button>
      </div>

      <div className="flex gap-3 mb-6">
        <div className="input-with-icon input-flex">
          <Search size={15} className="icon-left" />
          <input className="library-input with-pad input-small"
                 placeholder="Search name or email…"
                 value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <label className="filters-label">
          <input type="checkbox" checked={activeOnly} onChange={e => { setActiveOnly(e.target.checked); setPage(1); }} />
          Active only
        </label>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <div className="table-wrap">
        {loading ? (
          <div className="loading-empty">Loading…</div>
        ) : members.length === 0 ? (
          <div className="loading-empty">No members found.</div>
        ) : (
          <DataTable<Member>
            columns={[
              { key: 'name', title: 'Name', render: (m) => <div className="cell-strong">{m.name}</div> },
              { key: 'email', title: 'Email', render: (m) => <div className="cell-muted">{m.email}</div> },
              { key: 'phone', title: 'Phone', render: (m) => m.phone || '—' },
              { key: 'since', title: 'Member Since', render: (m) => new Date(m.membership_date).toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric' }) },
              { key: 'active_loans', title: 'Active Loans', className: 'text-center', render: (m) => m.active_loans },
              { key: 'status', title: 'Status', render: (m) => (
                <span className={`badge ${m.is_active ? 'badge-available' : 'badge-unavail'}`}>{m.is_active ? 'Active' : 'Inactive'}</span>
              )},
              { key: 'actions', title: '', render: (m) => (
                <div className="action-row">
                  <button className="btn btn-ghost btn-sm" onClick={() => { setSelected(m); setModal('edit'); }}><Pencil size={13}/></button>
                  <button className="btn btn-ghost btn-sm" title={m.is_active ? 'Deactivate' : 'Activate'} onClick={() => handleToggleActive(m)}>
                    {m.is_active ? <UserX size={13} className="icon-danger"/> : <UserCheck size={13} className="icon-ok"/>}
                  </button>
                  <button className="btn btn-ghost btn-sm text-danger" onClick={() => handleDelete(m)}><Trash2 size={13}/></button>
                </div>
              )},
            ]}
            data={members}
            rowKey={(r) => (r as any).id}
          />
        )}
      </div>

      {pages > 1 && (
        <div className="pagination">
          <button className="btn btn-ghost btn-sm" disabled={page === 1} onClick={() => setPage(p => p-1)}>← Prev</button>
          <span className="small-muted">Page {page} of {pages}</span>
          <button className="btn btn-ghost btn-sm" disabled={page === pages} onClick={() => setPage(p => p+1)}>Next →</button>
        </div>
      )}

      <ModalForm open={!!modal} title={modal === 'create' ? 'Register New Member' : 'Edit Member'} onClose={() => setModal(null)}>
        <MemberModal member={selected} onClose={() => setModal(null)} onSaved={() => { setModal(null); load(); onAction(); }} />
      </ModalForm>
      {/* Using UIProvider confirm/toast - no local dialogs here */}
    </div>
  );
}

// ── Member Modal ────────────────────────────────────────────────────────────
function MemberModal({ member, onClose, onSaved }: { member: Member | null; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({
    name: member?.name ?? '', email: member?.email ?? '',
    phone: member?.phone ?? '', address: member?.address ?? '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState('');

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async () => {
    setSaving(true); setError('');
    const payload: any = {
      name: form.name.trim(), email: form.email.trim(),
      phone: form.phone?.trim() || null, address: form.address?.trim() || null,
    };
    try {
      if (member) await membersApi.update(member.id, payload);
      else         await membersApi.create(payload);
      onSaved();
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box modal-max-600" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{member ? 'Edit Member' : 'Register New Member'}</h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm"><X size={16}/></button>
        </div>
        <div className="modal-content">
          {error && <div className="modal-error">{error}</div>}
          {[
            { label:'Full Name *', key:'name' },
            { label:'Email Address *', key:'email' },
            { label:'Phone', key:'phone' },
          ].map(({ label, key }) => (
            <div key={key}>
              <label className="form-label">{label}</label>
              <input className="library-input" value={(form as any)[key]} onChange={set(key)} />
            </div>
          ))}
          <div>
            <label className="form-label">Address</label>
            <textarea className="library-input" rows={2} value={form.address} onChange={set('address')} />
          </div>
        </div>
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving || !form.name.trim() || !form.email.trim()}>
            {saving ? 'Saving…' : member ? 'Save Changes' : 'Register Member'}
          </button>
        </div>
      </div>
    </div>
  );
}
