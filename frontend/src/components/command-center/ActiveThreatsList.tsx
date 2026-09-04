import React from 'react';
import { AlertOctagon, ArrowRight, ShieldAlert, Users, CreditCard, Laptop, ShieldCheck } from 'lucide-react';
import { useIncidents } from '../../hooks/useIncidents';

interface ActiveThreatsListProps {
  onSelectInvestigation: (investigationId: string) => void;
}

export const ActiveThreatsList: React.FC<ActiveThreatsListProps> = ({ onSelectInvestigation }) => {
  const { incidents, loading, error } = useIncidents(5000);

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 font-mono text-xs">
      <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <span>Active Incident Matrix</span>
          </h2>
          <p className="text-[11px] text-slate-400">
            Real-time analyst work queue backed by <code className="text-indigo-300">GET /api/v1/investigations/active</code>
          </p>
        </div>
        {incidents.length > 0 ? (
          <span className="text-[10px] px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1.5 animate-pulse font-bold">
            <AlertOctagon className="w-3.5 h-3.5" />
            <span>{incidents.length} ACTIVE INCIDENTS</span>
          </span>
        ) : (
          <span className="text-[10px] px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 font-bold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>0 ACTIVE INCIDENTS</span>
          </span>
        )}
      </div>

      {loading && incidents.length === 0 ? (
        <div className="p-6 text-center text-slate-500 font-mono animate-pulse">
          Fetching active incident queue from risk engine...
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 text-rose-400 text-center font-mono">
          Failed to load active incidents: {error}
        </div>
      ) : incidents.length === 0 ? (
        <div className="p-8 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-2">
          <ShieldCheck className="w-8 h-8 text-emerald-400 mx-auto" />
          <h3 className="text-sm font-bold text-slate-200">No Active Threats Detected</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto font-sans leading-relaxed">
            All evaluated transaction streams are operating within low-risk thresholds. Ingest a high-risk transaction or trigger an attack scenario in the Threat Simulator to populate this operational queue.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3.5">
          {incidents.map((incident) => (
            <div
              key={incident.incident_id}
              onClick={() => onSelectInvestigation(incident.incident_id)}
              className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-indigo-500/60 transition-all cursor-pointer space-y-3 group"
            >
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-200 group-hover:text-indigo-400 transition-colors">
                      {incident.name}
                    </h3>
                    <p className="text-[10px] font-mono text-slate-500">{incident.incident_id}</p>
                  </div>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30">
                  {incident.severity} ({incident.risk_score})
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[10px] font-mono bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                <div>
                  <span className="text-slate-500 block">Exposure</span>
                  <span className="text-emerald-400 font-bold">{incident.exposure}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Nodes</span>
                  <span className="text-slate-300 font-bold">{incident.affected_entities} Nodes</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Confidence</span>
                  <span className="text-indigo-400 font-bold">{incident.confidence}%</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] text-indigo-400 font-medium pt-1">
                <span className="text-[10px] font-mono text-slate-400 truncate max-w-[200px]">
                  {incident.detected_patterns}
                </span>
                <span className="flex items-center gap-1 group-hover:translate-x-1 transition-transform shrink-0 font-bold">
                  Inspect <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
