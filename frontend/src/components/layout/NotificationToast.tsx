import React from 'react';
import { useNotification, ToastMessage } from '../../providers/NotificationProvider';
import { AlertTriangle, CheckCircle, Info, XCircle, X } from 'lucide-react';

export const NotificationToast: React.FC = () => {
  const { toasts, removeToast } = useNotification();

  if (toasts.length === 0) return null;

  const getIcon = (type: ToastMessage['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-rose-400" />;
      default:
        return <Info className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="pointer-events-auto flex items-start gap-3 p-3.5 rounded-lg bg-slate-900/95 border border-slate-800 backdrop-blur-md shadow-xl text-xs text-slate-200 transition-all transform animate-in slide-in-from-bottom-2"
        >
          <div className="mt-0.5 shrink-0">{getIcon(toast.type)}</div>
          <div className="flex-1 space-y-0.5">
            <p className="font-semibold text-slate-100">{toast.title}</p>
            <p className="text-slate-400 text-[11px] leading-relaxed">{toast.message}</p>
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-slate-500 hover:text-slate-300 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
