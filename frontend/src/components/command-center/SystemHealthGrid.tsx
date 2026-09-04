import React from 'react';
import { Cpu, Database, Network, BrainCircuit, Shield, CheckCircle2, AlertOctagon, XCircle } from 'lucide-react';
import { SystemStatusData } from '../../types/domain';

interface SystemHealthGridProps {
  systemStatus: SystemStatusData | null;
}

export const SystemHealthGrid: React.FC<SystemHealthGridProps> = ({ systemStatus }) => {
  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'HEALTHY':
        return (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>HEALTHY</span>
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <AlertOctagon className="w-3 h-3 text-amber-400" />
            <span>DEGRADED</span>
          </span>
        );
      case 'OFFLINE':
        return (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 animate-pulse">
            <XCircle className="w-3 h-3 text-rose-400" />
            <span>OFFLINE</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            UNKNOWN
          </span>
        );
    }
  };

  const services = [
    {
      name: 'Risk Engine',
      key: 'risk_engine',
      desc: 'Real-time multi-tier transaction scoring & threat aggregation',
      icon: Cpu,
    },
    {
      name: 'IsolationForest ML',
      key: 'ml_engine',
      desc: 'AI-based statistical fraud anomaly & outlier detector',
      icon: BrainCircuit,
    },
    {
      name: 'Multi-Hop Graph Engine',
      key: 'graph_engine',
      desc: 'Detects mule rings & linked criminal device clusters',
      icon: Network,
    },
    {
      name: 'Gemini 3.6 AI Reasoning',
      key: 'gemini',
      desc: 'Grounded AI investigator explaining fraud evidence & risk',
      icon: BrainCircuit,
    },
    {
      name: 'Redis Fast Velocity Store',
      key: 'redis',
      desc: 'Sub-millisecond card & IP velocity counter database',
      icon: Database,
    },
    {
      name: 'PostgreSQL Relational DB',
      key: 'postgres',
      desc: 'Persistent storage for transaction & incident records',
      icon: Database,
    },
    {
      name: 'Cryptographic Audit Ledger',
      key: 'audit',
      desc: 'SHA-256 tamper-proof ledger for complete audit trail',
      icon: Shield,
    },
    {
      name: 'Fail-Closed Action Gateway',
      key: 'action_gateway',
      desc: 'Enforces HMAC action tokens to prevent unauthorized blocks',
      icon: Shield,
    },
  ];

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800/80 pb-3 gap-2">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <span>System Protection Matrix & Health Monitor</span>
          </h2>
          <p className="text-[11px] text-slate-400">
            Real-time operational status for all core security modules (<code className="font-mono text-indigo-400">GET /api/v1/system/status</code>)
          </p>
        </div>
        <div className="text-xs font-mono px-3 py-1 rounded-lg bg-slate-950 text-slate-300 border border-slate-800 flex items-center gap-2 w-fit">
          <span>Defense System:</span>
          <span className={systemStatus ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
            {systemStatus ? "FULLY OPERATIONAL" : "BACKEND OFFLINE"}
          </span>
        </div>
      </div>

      {systemStatus === null && (
        <div className="p-3.5 rounded-lg bg-rose-950/30 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-center justify-between">
          <span>⚠️ Backend Telemetry Unreachable. Start backend API server (`python -m backend.app.main`) to populate live component status.</span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {services.map((svc) => {
          const Icon = svc.icon;
          const statusVal = systemStatus ? systemStatus.components?.[svc.key as keyof typeof systemStatus.components] : 'UNKNOWN';
          return (
            <div key={svc.key} className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2 hover:border-slate-700 transition-all">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-indigo-400 shrink-0" />
                  <span className="text-xs font-bold text-slate-200">{svc.name}</span>
                </div>
                {getStatusBadge(statusVal)}
              </div>
              <p className="text-[11px] text-slate-400 leading-normal">{svc.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

