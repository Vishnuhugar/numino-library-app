import React from 'react';

export default function ConfirmDialog({ open, title, message, onConfirm, onCancel }: {
  open: boolean;
  title?: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-box modal-max-420" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">{title ?? 'Confirm'}</h3>
        </div>
        <div className="modal-content">
          <div className="modal-body">{message}</div>
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={onCancel}>Cancel</button>
            <button className="btn btn-primary" onClick={onConfirm}>Confirm</button>
          </div>
        </div>
      </div>
    </div>
  );
}
