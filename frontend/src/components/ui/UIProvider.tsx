"use client";
import React, { createContext, useCallback, useContext, useState } from 'react';
import ConfirmDialog from './ConfirmDialog';
import Toast from './Toast';

type ConfirmOpts = { title?: string; message: string };

interface UIContextValue {
  showToast: (message: string) => void;
  confirm: (opts: ConfirmOpts) => Promise<boolean>;
}

const UIContext = createContext<UIContextValue | null>(null);

export function UIProvider({ children }: { children: React.ReactNode }) {
  const [toast, setToast] = useState<string | null>(null);
  const [confirmState, setConfirmState] = useState<null | (ConfirmOpts & { resolve: (v: boolean) => void })>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
  }, []);

  const confirm = useCallback((opts: ConfirmOpts) => {
    return new Promise<boolean>((resolve) => {
      setConfirmState({ ...opts, resolve });
    });
  }, []);

  const handleConfirm = (ok: boolean) => {
    if (!confirmState) return;
    try { confirmState.resolve(ok); }
    finally { setConfirmState(null); }
  };

  return (
    <UIContext.Provider value={{ showToast, confirm }}>
      {children}
      <ConfirmDialog open={!!confirmState} title={confirmState?.title} message={confirmState?.message ?? ''}
        onConfirm={() => handleConfirm(true)} onCancel={() => handleConfirm(false)} />
      <Toast message={toast} onClose={() => setToast(null)} />
    </UIContext.Provider>
  );
}

export function useUI() {
  const ctx = useContext(UIContext);
  if (!ctx) throw new Error('useUI must be used within UIProvider');
  return ctx;
}

export default UIContext;
