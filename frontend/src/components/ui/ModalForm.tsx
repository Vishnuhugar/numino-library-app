"use client";
import React from 'react';
import { X } from 'lucide-react';

export default function ModalForm({ open, title, children, onClose, footer }: {
  open: boolean; title?: string; children: React.ReactNode; onClose: () => void; footer?: React.ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box modal-max-600" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{title}</h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm"><X size={16} /></button>
        </div>
        <div className="modal-content">
          {children}
        </div>
        {footer && <div className="modal-actions">{footer}</div>}
      </div>
    </div>
  );
}
