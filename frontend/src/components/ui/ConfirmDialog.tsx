"use client";
import React from 'react';
import { X } from 'lucide-react';

export default function ConfirmDialog({ open, title, message, onConfirm, onCancel }: {
  open: boolean; title?: string; message: string; onConfirm: () => void; onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-box modal-max-420" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{title || 'Confirm'}</h2>
          <button onClick={onCancel} className="btn btn-ghost btn-sm"><X size={16} /></button>
        </div>
        <div className="modal-content">
          <div className="confirm-message">{message}</div>
        </div>
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onCancel}>Cancel</button>
          <button className="btn btn-primary" onClick={onConfirm}>Confirm</button>
        </div>
      </div>
    </div>
  );
}
