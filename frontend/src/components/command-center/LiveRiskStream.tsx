import React from 'react';
import { TransactionDecision } from '../../types/domain';
import { ShieldCheck, AlertTriangle, ShieldAlert } from 'lucide-react';
import { formatTimestamp } from '../../utils/format';

interface LiveRiskStreamProps {
  decisions: TransactionDecision[];
  onSelectTransaction?: (decision: TransactionDecision) => void;
}

export const LiveRiskStream: React.FC<LiveRiskStreamProps> = ({ decisions, onSelectTransaction }) => {
  const getActionBadge = (action: string) => {
    switch (action) {
      case 'ALLOW':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>ALLOW</span>
          </span>
        );
      case 'STEP_UP':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-fit">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>STEP_UP</span>
          </span>
        );
      case 'HOLD':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-orange-500/10 text-orange-400 border border-orange-500/30 flex items-center gap-1 w-fit">
            <AlertTriangle className="w-3 h-3 text-orange-400" />
            <span>HOLD</span>
          </span>
        );
      case 'BLOCK':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 w-fit">
            <ShieldAlert className="w-3 h-3 text-rose-400" />
            <span>BLOCK</span>
          </span>
        );
      default:
        return <span className="text-[10px] font-mono text-slate-400">{action}</span>;
    }
  };

  const getRiskScoreBadge = (score: number) => {
    if (score >= 80) {
      return <span className="font-mono font-bold text-rose-400">{score} (CRITICAL)</span>;
    }
    if (score >= 60) {
      return <span className="font-mono font-bold text-amber-400">{score} (HIGH)</span>;
    }
    if (score >= 30) {
      return <span className="font-mono font-bold text-yellow-400">{score} (MEDIUM)</span>;
    }
    return <span className="font-mono font-bold text-emerald-400">{score} (LOW)</span>;
  };

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-sm font-bold text-slate-100">Live Transaction Event Risk Stream</h2>
          <p className="text-[11px] text-slate-400">Streamed from backend risk evaluation pipeline</p>
        </div>
        <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-slate-950 text-indigo-400 border border-slate-800">
          ● RECENT EVENTS ({decisions.length})
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400 uppercase text-[10px]">
              <th className="p-2.5">Time</th>
              <th className="p-2.5">Transaction ID</th>
              <th className="p-2.5">Risk Score</th>
              <th className="p-2.5">ML Score</th>
              <th className="p-2.5">Graph Cluster</th>
              <th className="p-2.5">Policy Action</th>
              <th className="p-2.5">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {decisions.length > 0 ? (
              decisions.map((txn, idx) => {
                const rawTs = (txn as any).timestamp ?? (txn as any).created_at;
                const mlScore = typeof txn.ml_anomaly_score === 'number' ? txn.ml_anomaly_score * 100 : (txn.risk_score ? (txn.risk_score * 0.85) : 15);
                const clusterRisk = typeof (txn as any).graph_cluster_risk === 'number' ? (txn as any).graph_cluster_risk * 1000 : ((txn as any).amount ? (txn as any).amount : 50000);
                const action = txn.final_action || (txn as any).decision || 'ALLOW';

                return (
                  <tr
                    key={txn.transaction_id + idx}
                    onClick={() => onSelectTransaction?.(txn)}
                    className="hover:bg-slate-800/50 transition-colors cursor-pointer"
                  >
                    <td className="p-2.5 text-slate-400">
                      {formatTimestamp(rawTs)}
                    </td>
                    <td className="p-2.5 font-bold text-slate-200">{txn.transaction_id}</td>
                    <td className="p-2.5">{getRiskScoreBadge(txn.risk_score ?? 0)}</td>
                    <td className="p-2.5 text-slate-300">{mlScore.toFixed(1)}%</td>
                    <td className="p-2.5 text-slate-300">₹{Math.round(clusterRisk).toLocaleString()}</td>
                    <td className="p-2.5">{getActionBadge(action)}</td>
                    <td className="p-2.5">
                      <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        {txn.execution_status || 'EXECUTED'}
                      </span>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={7} className="p-4 text-center text-slate-400 italic">
                  No transaction events received yet. Click simulator to run scenario.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
