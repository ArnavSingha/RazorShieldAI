import React from 'react';
import { InvestigationPackage } from '../../types/domain';
import { ShieldAlert, AlertTriangle, CheckCircle, Clock, Users, IndianRupee } from 'lucide-react';

interface IncidentHeaderProps {
  packageData: InvestigationPackage | null;
}

export const IncidentHeader: React.FC<IncidentHeaderProps> = ({ packageData }) => {
  if (!packageData) {
    return (
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 animate-pulse text-xs text-slate-400">
        Loading investigation package...
      </div>
    );
  }

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return (
          <span className="px-2.5 py-1 rounded text-xs font-mono font-extrabold bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1.5 animate-pulse">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>CRITICAL INCIDENT</span>
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2.5 py-1 rounded text-xs font-mono font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>HIGH RISK</span>
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>LOW RISK</span>
          </span>
        );
    }
  };

  return (
    <div className="p-5 rounded-xl bg-slate-900/95 border border-slate-800 shadow-xl space-y-4">
      <div className="flex justify-between items-start">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            {getSeverityBadge(packageData.severity)}
            <h2 className="text-base font-mono font-bold text-slate-100">{packageData.incident_id}</h2>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-slate-800 text-indigo-400 border border-slate-700">
              PKG: {packageData.package_id}
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Target Seed Entity: <code className="text-indigo-300 font-bold">{packageData.entity_id}</code> • Time Window: {packageData.time_window || 'Last 24h'}
          </p>
        </div>

        <div className="flex items-center gap-4 text-right">
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono">
            <span className="text-[10px] text-slate-400 block uppercase">Cluster Risk Score</span>
            <span className="text-xl font-bold text-rose-400">{packageData.risk_score ?? 75} / 100</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono">
            <span className="text-[10px] text-slate-400 block uppercase">Confidence</span>
            <span className="text-xl font-bold text-indigo-400">{packageData.confidence_score ?? 94}%</span>
          </div>
        </div>
      </div>

      {/* Key Metrics Bar */}
      <div className="grid grid-cols-4 gap-3 pt-2 font-mono text-xs">
        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <Users className="w-4 h-4 text-indigo-400" />
            <span>Affected Accounts</span>
          </div>
          <span className="text-slate-100 font-bold">{packageData.affected_accounts_count || packageData.nodes?.length || 4} Nodes</span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <IndianRupee className="w-4 h-4 text-emerald-400" />
            <span>Financial Exposure</span>
          </div>
          <span className="text-emerald-400 font-bold">₹{packageData.total_financial_exposure_inr?.toLocaleString() || '310,000'}</span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <Clock className="w-4 h-4 text-amber-400" />
            <span>Evidence Hash</span>
          </div>
          <span className="text-slate-300 font-mono text-[10px] truncate max-w-[120px]" title={packageData.evidence_snapshot_hash}>
            {packageData.evidence_snapshot_hash?.substring(0, 12)}...
          </span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>Detected Patterns</span>
          </div>
          <span className="text-rose-400 font-bold text-[11px]">
            {packageData.detected_patterns?.length || 3} Active Rules
          </span>
        </div>
      </div>
    </div>
  );
};
