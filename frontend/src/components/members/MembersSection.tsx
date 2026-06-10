'use client';

import { useState, useEffect, useCallback } from 'react';
import { Plus, Search, Pencil, Trash2, X, UserCheck, UserX } from 'lucide-react';
import { membersApi, type Member } from '@/lib/api';

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
      const r = await membersApi.list({ page, size: SIZE, search: search || undefined, active_only: activeOnly });
      setMembers(r.items); setTotal(r.total);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }, [page, search, activeOnly]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (m: Member) => {
    if (!confirm(`Remove member "${m.name}"?`)) return;
    try { await membersApi.delete(m.id); load(); onAction(); }
    catch (e: any) { alert(e.message); }
  };

  const handleToggleActive = async (m: Member) => {
    try { await membersApi.update(m.id, { is_active: !m.is_active }); load(); }
    catch (e: any) { alert(e.message); }
  };

  const pages = Math.max(1, Math.ceil(total / SIZE));

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontFamily:"'Playfair Display',serif", fontSize:'1.8rem' }}>Members</h1>
          <div style={{ color:'rgba(26,18,8,0.5)', fontFamily:"'Crimson Text',serif" }}>
            {total} registered member{total !== 1 ? 's' : ''}
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => { setSelected(null); setModal('create'); }}>
          <Plus size={16}/> Add Member
        </button>
      </div>

      <div className="flex gap-3 mb-6">
        <div style={{ position:'relative', flex:1, maxWidth:360 }}>
          <Search size={15} style={{ position:'absolute', left:10, top:'50%', transform:'translateY(-50%)', color:'rgba(26,18,8,0.4)' }} />
          <input className="library-input" style={{ paddingLeft:32 }}
                 placeholder="Search name or email…"
                 value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <label style={{ display:'flex', alignItems:'center', gap:6, fontFamily:"'Crimson Text',serif", cursor:'pointer' }}>
          <input type="checkbox" checked={activeOnly} onChange={e => { setActiveOnly(e.target.checked); setPage(1); }} />
          Active only
        </label>
      </div>

      {error && <div style={{ color:'#8b1a1a', marginBottom:12 }}>{error}</div>}

      <div style={{ background:'rgba(253,246,227,0.7)', border:'1px solid rgba(200,151,42,0.2)', borderRadius:2 }}>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'rgba(26,18,8,0.4)', fontFamily:"'Crimson Text',serif" }}>Loading…</div>
        ) : members.length === 0 ? (
          <div style={{ padding:40, textAlign:'center', color:'rgba(26,18,8,0.4)', fontFamily:"'Crimson Text',serif" }}>No members found.</div>
        ) : (
          <table className="lib-table">
            <thead>
              <tr>
                <th>Name</th><th>Email</th><th>Phone</th>
                <th>Member Since</th><th style={{ textAlign:'center' }}>Active Loans</th>
                <th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {members.map(m => (
                <tr key={m.id}>
                  <td style={{ fontWeight:600 }}>{m.name}</td>
                  <td style={{ color:'rgba(26,18,8,0.7)' }}>{m.email}</td>
                  <td style={{ color:'rgba(26,18,8,0.6)' }}>{m.phone || '—'}</td>
                  <td style={{ fontSize:'0.88rem', color:'rgba(26,18,8,0.55)' }}>
                    {new Date(m.membership_date).toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric' })}
                  </td>
                  <td style={{ textAlign:'center' }}>{m.active_loans}</td>
                  <td>
                    <span className={`badge ${m.is_active ? 'badge-available' : 'badge-unavail'}`}>
                      {m.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display:'flex', gap:6 }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => { setSelected(m); setModal('edit'); }}><Pencil size={13}/></button>
                      <button className="btn btn-ghost btn-sm" title={m.is_active ? 'Deactivate' : 'Activate'} onClick={() => handleToggleActive(m)}>
                        {m.is_active ? <UserX size={13} style={{ color:'#8b1a1a' }}/> : <UserCheck size={13} style={{ color:'#2d5016' }}/>}
                      </button>
                      <button className="btn btn-ghost btn-sm" style={{ color:'#8b1a1a' }} onClick={() => handleDelete(m)}><Trash2 size={13}/></button>
                    </div>
                  </td>
                </tr>
              ))}
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
        <MemberModal
          member={selected}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); load(); onAction(); }}
        />
      )}
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
      name: form.name, email: form.email,
      phone: form.phone || null, address: form.address || null,
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
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div style={{ padding:'24px 28px', borderBottom:'1px solid rgba(200,151,42,0.2)', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
          <h2 style={{ fontFamily:"'Playfair Display',serif", fontSize:'1.3rem' }}>
            {member ? 'Edit Member' : 'Register New Member'}
          </h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm"><X size={16}/></button>
        </div>
        <div style={{ padding:'24px 28px', display:'flex', flexDirection:'column', gap:14 }}>
          {error && <div style={{ color:'#8b1a1a', fontFamily:"'Crimson Text',serif" }}>{error}</div>}
          {[
            { label:'Full Name *', key:'name' },
            { label:'Email Address *', key:'email' },
            { label:'Phone', key:'phone' },
          ].map(({ label, key }) => (
            <div key={key}>
              <label style={{ display:'block', fontFamily:"'Crimson Text',serif", fontWeight:600, marginBottom:4, fontSize:'0.9rem', color:'rgba(26,18,8,0.7)' }}>{label}</label>
              <input className="library-input" value={(form as any)[key]} onChange={set(key)} />
            </div>
          ))}
          <div>
            <label style={{ display:'block', fontFamily:"'Crimson Text',serif", fontWeight:600, marginBottom:4, fontSize:'0.9rem', color:'rgba(26,18,8,0.7)' }}>Address</label>
            <textarea className="library-input" rows={2} value={form.address} onChange={set('address')} />
          </div>
        </div>
        <div style={{ padding:'16px 28px', borderTop:'1px solid rgba(200,151,42,0.2)', display:'flex', gap:10, justifyContent:'flex-end' }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving || !form.name || !form.email}>
            {saving ? 'Saving…' : member ? 'Save Changes' : 'Register Member'}
          </button>
        </div>
      </div>
    </div>
  );
}
