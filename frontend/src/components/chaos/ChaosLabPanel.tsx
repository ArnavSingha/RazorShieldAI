import React from 'react';
import { useChaosController } from '../../hooks/useChaosController';
import { Flame, ShieldAlert, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';

export const ChaosLabPanel: React.FC = () => {
  const { chaosStatus, toggleFault, refetch } = useChaosController();
  const { addToast } = useNotification();

  const handleToggle = async (faultKey: string, enable: boolean) => {
    await toggleFault(faultKey, enable);
    if (enable) {
      addToast(
        faultKey === 'AUDIT_OFFLINE' ? 'error' : 'warning',
        `Fault Activated: ${faultKey}`,
        faultKey === 'AUDIT_OFFLINE'
          ? 'AUDIT_OFFLINE active! Triggered FAIL-CLOSED execution block (Unsafe Actions = 0).'
          : `Dependency fault ${faultKey} activated. System operating in degraded mode.`
      );
    } else {
      addToast('success', `Fault Cleared: ${faultKey}`, `Dependency fault ${faultKey} deactivated. System restored to healthy state.`);
    }
  };

  const faults = [
    { key: 'GEMINI_OFFLINE', name: 'Gemini LLM Provider Offline', desc: 'Triggers automatic fallback to Deterministic Policy Engine with 0% downtime.' },
    { key: 'ML_OFFLINE', name: 'IsolationForest ML Offline', desc: 'Degrades ML scoring weight to 0.0 while preserving Rule & Graph evaluations.' },
    { key: 'GRAPH_OFFLINE', name: 'Multi-Hop Graph Engine Offline', desc: 'Bypasses multi-hop graph cluster search; falls back to stateful velocity rules.' },
    { key: 'REDIS_OFFLINE', name: 'Redis Cache Unreachable', desc: 'Fails fast in production simulation or uses local memory fallback.' },
    { key: 'POSTGRES_OFFLINE', name: 'PostgreSQL Unreachable', desc: 'Fails fast; prevents un-audited state mutation.' },
    { key: 'AUDIT_OFFLINE', name: 'Cryptographic Audit Offline', desc: 'Triggers FAIL-CLOSED action gate. All transaction executions are REJECTED.' },
    { key: 'GATEWAY_OFFLINE', name: 'Action Gateway Offline', desc: 'Rejects signed ActionTokens; enforces safety invariant UNSAFE ACTIONS = 0.' },
  ];

  const activeFaults = chaosStatus.active_faults || [];
  const isAuditOffline = activeFaults.includes('AUDIT_OFFLINE');

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-rose-400" />
            <div>
              <h2 className="text-sm font-bold text-slate-100">Chaos Engineering & Resilience Lab</h2>
              <p className="text-[11px] text-slate-400">
                Interactive dependency fault toggles backed by <code className="text-indigo-300">POST /api/v1/simulator/chaos/toggle</code>
              </p>
            </div>
          </div>
          <button
            onClick={() => refetch()}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono flex items-center gap-1 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh State</span>
          </button>
        </div>

        {/* DEPENDENCY TOPOLOGY DIAGRAM */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4 text-center font-mono">
          <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
            Dependency Topology & Resilience Flow
          </p>
          <div className="flex justify-center items-center gap-6 text-xs">
            <div className="p-3 rounded-lg bg-indigo-950/60 border border-indigo-500/40 text-indigo-300 font-bold">
              RAZORSHIELD CORE
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto text-xs">
            <div className={`p-2.5 rounded-lg border ${activeFaults.includes('GEMINI_OFFLINE') ? 'bg-rose-950/40 border-rose-500/40 text-rose-400' : 'bg-slate-900 border-slate-800 text-slate-300'}`}>
              ↓ GEMINI LLM
            </div>
            <div className={`p-2.5 rounded-lg border ${activeFaults.includes('ML_OFFLINE') ? 'bg-rose-950/40 border-rose-500/40 text-rose-400' : 'bg-slate-900 border-slate-800 text-slate-300'}`}>
              ↓ ISOLATION FOREST ML
            </div>
            <div className={`p-2.5 rounded-lg border ${activeFaults.includes('GRAPH_OFFLINE') ? 'bg-rose-950/40 border-rose-500/40 text-rose-400' : 'bg-slate-900 border-slate-800 text-slate-300'}`}>
              ↓ MULTI-HOP GRAPH
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto text-xs">
            <div className={`p-2.5 rounded-lg border ${activeFaults.includes('REDIS_OFFLINE') ? 'bg-rose-950/40 border-rose-500/40 text-rose-400' : 'bg-slate-900 border-slate-800 text-slate-300'}`}>
              ↓ REDIS CACHE
            </div>
            <div className={`p-2.5 rounded-lg border ${activeFaults.includes('POSTGRES_OFFLINE') ? 'bg-rose-950/40 border-rose-500/40 text-rose-400' : 'bg-slate-900 border-slate-800 text-slate-300'}`}>
              ↓ POSTGRESQL DB
            </div>
            <div className={`p-2.5 rounded-lg border ${activeFaults.includes('AUDIT_OFFLINE') ? 'bg-rose-950/40 border-rose-500/40 text-rose-400' : 'bg-slate-900 border-slate-800 text-slate-300'}`}>
              ↓ AUDIT LEDGER
            </div>
          </div>
        </div>

        {/* FAULT TOGGLE GRID */}
        <div className="grid grid-cols-4 gap-4">
          {faults.map((fault) => {
            const isActive = activeFaults.includes(fault.key);
            return (
              <div
                key={fault.key}
                className={`p-4 rounded-xl border transition-all ${
                  isActive
                    ? 'bg-rose-950/30 border-rose-500/50 shadow-lg shadow-rose-500/10'
                    : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs font-mono font-bold text-slate-200 block">{fault.key}</span>
                    <span className="text-[10px] text-slate-400 font-sans">{fault.name}</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => handleToggle(fault.key, e.target.checked)}
                    className="w-4 h-4 text-indigo-600 bg-slate-900 border-slate-700 rounded cursor-pointer accent-indigo-500"
                  />
                </div>
                <p className="text-[10px] text-slate-400 leading-normal mt-2 font-sans">{fault.desc}</p>
                <div className="mt-3 pt-2 border-t border-slate-900 flex justify-between items-center text-[10px] font-mono">
                  <span className="text-slate-500">Status:</span>
                  <span className={isActive ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                    {isActive ? '● FAULT ACTIVE' : '● HEALTHY'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* FAIL-CLOSED DEMONSTRATION BOX */}
      {isAuditOffline && (
        <div className="p-5 rounded-xl bg-rose-950/40 border-2 border-rose-500/60 space-y-3 font-mono text-xs shadow-2xl animate-pulse">
          <div className="flex items-center gap-2 text-rose-400 font-bold">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>CRITICAL RESILIENCE INVARIANT DEMONSTRATION: FAIL-CLOSED</span>
          </div>
          <div className="space-y-1 text-slate-300 leading-relaxed font-sans">
            <p>
              Fault <code className="text-rose-300 font-mono font-bold">AUDIT_OFFLINE</code> is currently active. The RazorShield Action Gateway has automatically triggered a <strong>FAIL-CLOSED</strong> execution block.
            </p>
            <p>
              Execution Status: <span className="text-rose-400 font-mono font-bold">REJECTED</span> • Reason Code: <span className="text-rose-400 font-mono font-bold">AUDIT_UNAVAILABLE</span> • Unsafe Actions: <span className="text-emerald-400 font-mono font-bold">0</span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
