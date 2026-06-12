import React, { useEffect } from 'react';

export default function Toast({ message, onClose }: { message: string | null; onClose: () => void }) {
  useEffect(() => {
    if (!message) return;
    const t = setTimeout(onClose, 3500);
    return () => clearTimeout(t);
  }, [message, onClose]);

  if (!message) return null;
  return (
    <div className="toast-container">
      <div className="toast-message">{message}</div>
    </div>
  );
}
