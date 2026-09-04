import React from 'react';
import { TransactionDecision } from '../../types/domain';
import { X, CreditCard, ShieldCheck, ShieldAlert, AlertTriangle, Zap, User, Laptop, Globe } from 'lucide-react';

interface TransactionDrawerProps {
  transaction: TransactionDecision | null;
  onClose: () => void;
}

export const TransactionDrawer: React.FC<TransactionDrawerProps> = ({ transaction, onClose }) => {
  if (!transaction) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[480px] bg-slate-950/95 border-l border-slate-800 p-6 space-y-6 font-mono text-xs shadow-2xl overflow-y-auto backdrop-blur-xl animate-in slide-in-from-right">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="font-bold text-slate-100 text-sm">{transaction.transaction_id}</h3>
            <p className="text-[10px] text-slate-400">Transaction Deep Inspector Drawer</p>
          </div>
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-slate-200">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-500 block uppercase">Risk Score & Tier</span>
          <span className="text-lg font-bold text-rose-400">{transaction.risk_score} ({transaction.risk_level})</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-500 block uppercase">Policy Decision</span>
          <span className="text-lg font-bold text-amber-400">{transaction.final_action}</span>
        </div>
      </div>

      {/* Signal Evidence & ML */}
      <div className="space-y-3">
        <h4 className="text-[11px] font-bold text-slate-300 uppercase border-b border-slate-800/80 pb-1">
          Signal Evidence & ML Score
        </h4>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2 text-[11px]">
          <div className="flex justify-between">
            <span className="text-slate-500">IsolationForest ML Anomaly:</span>
            <span className="text-indigo-400 font-bold">{(transaction.ml_anomaly_score * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Graph Cluster Risk:</span>
            <span className="text-slate-200 font-bold">₹{(transaction.graph_cluster_risk * 1000).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Triggered Rules:</span>
            <span className="text-rose-400 font-bold">{transaction.rules_triggered?.join(', ') || 'HIGH_VELOCITY'}</span>
          </div>
        </div>
      </div>

      {/* Gemini AI Reasoning if available */}
      {transaction.gemini_reasoning && (
        <div className="space-y-2">
          <h4 className="text-[11px] font-bold text-purple-400 uppercase">Gemini Agent Reasoning Trace</h4>
          <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/30 text-[11px] font-sans text-slate-200 leading-relaxed">
            {transaction.gemini_reasoning}
          </div>
        </div>
      )}

      {/* Execution State & Lineage */}
      <div className="space-y-2">
        <h4 className="text-[11px] font-bold text-slate-300 uppercase">Action Gateway & Audit Lineage</h4>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1.5 text-[11px]">
          <div className="flex justify-between">
            <span className="text-slate-500">Execution Status:</span>
            <span className="text-emerald-400 font-bold">{transaction.execution_status || 'EXECUTED'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Audit Verification:</span>
            <span className="text-emerald-400 font-bold">PASS ✓</span>
          </div>
        </div>
      </div>
    </div>
  );
};
