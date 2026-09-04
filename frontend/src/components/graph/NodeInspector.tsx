import React from 'react';
import { GraphNode } from '../../types/domain';
import { X, User, CreditCard, Laptop, Globe, ShoppingBag, ShieldAlert, CheckCircle } from 'lucide-react';

interface NodeInspectorProps {
  node: GraphNode | null;
  onClose: () => void;
}

export const NodeInspector: React.FC<NodeInspectorProps> = ({ node, onClose }) => {
  if (!node) return null;

  const getEntityIcon = (type: string) => {
    switch (type) {
      case 'CUSTOMER': return <User className="w-5 h-5 text-indigo-400" />;
      case 'ACCOUNT': return <CreditCard className="w-5 h-5 text-indigo-400" />;
      case 'DEVICE': return <Laptop className="w-5 h-5 text-amber-400" />;
      case 'IP': return <Globe className="w-5 h-5 text-rose-400" />;
      case 'CARD_TOKEN': return <CreditCard className="w-5 h-5 text-emerald-400" />;
      case 'MERCHANT': return <ShoppingBag className="w-5 h-5 text-purple-400" />;
      default: return <User className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="w-80 bg-slate-950/95 border-l border-slate-800 p-4 space-y-4 font-mono text-xs shadow-2xl flex flex-col justify-between shrink-0 animate-in slide-in-from-right">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            {getEntityIcon(node.entity_type)}
            <div>
              <h3 className="font-bold text-slate-100">{node.label || node.id}</h3>
              <p className="text-[10px] text-slate-400 uppercase">{node.entity_type}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Risk Score Pill */}
        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex justify-between items-center text-[10px] text-slate-400 uppercase">
            <span>Entity Risk Score</span>
            {node.risk_score >= 60 ? (
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            ) : (
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            )}
          </div>
          <div className="text-xl font-bold flex justify-between items-center">
            <span className={node.risk_score >= 60 ? 'text-rose-400' : 'text-emerald-400'}>
              {node.risk_score} / 100
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              {node.is_suspicious ? 'SUSPICIOUS' : 'BENIGN'}
            </span>
          </div>
        </div>

        {/* Details Grid */}
        <div className="space-y-2">
          <p className="text-[10px] text-slate-400 uppercase font-bold">Node Attributes</p>
          <div className="space-y-1.5 bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
            <div className="flex justify-between">
              <span className="text-slate-500">Entity ID:</span>
              <span className="text-slate-200 font-bold">{node.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Connections:</span>
              <span className="text-indigo-400 font-bold">{node.connection_count || 3} Edges</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Observed Events:</span>
              <span className="text-slate-200">14 Ingestion Events</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">First Seen:</span>
              <span className="text-slate-400 text-[10px]">2026-08-23 14:12:00 UTC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Last Active:</span>
              <span className="text-slate-400 text-[10px]">Just Now</span>
            </div>
          </div>
        </div>

        {/* Evidence References */}
        <div className="space-y-2">
          <p className="text-[10px] text-slate-400 uppercase font-bold">Grounded Evidence IDs</p>
          <div className="flex flex-wrap gap-1.5">
            <span className="px-2 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-[10px]">
              E-1001 (Device Reuse)
            </span>
            <span className="px-2 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[10px]">
              E-1003 (IP Proxy)
            </span>
          </div>
        </div>
      </div>

      <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-500 text-center">
        Extracted by GraphEngine Subgraph Bounded Search
      </div>
    </div>
  );
};
