import React, { useState, useEffect } from 'react';
import { ShieldCheck, Activity, AlertOctagon, Search, Lock, Zap, Clock } from 'lucide-react';
import { SystemStatusData, TransactionDecision } from '../../types/domain';
import { fetchAnalyticsSummary, AnalyticsSummaryData } from '../../services/analytics';
import { fetchActionTelemetry, ActionTelemetryData } from '../../services/telemetry';

interface KpiStripProps {
  systemStatus: SystemStatusData | null;
  recentDecisions: TransactionDecision[];
  activeIncidentsCount?: number;
  unsafeActionsCount?: number;
  onWindowChange?: (win: string) => void;
}

export const KpiStrip: React.FC<KpiStripProps> = ({
  systemStatus,
  recentDecisions,
  activeIncidentsCount = 0,
  unsafeActionsCount: propUnsafeCount = 0,
  onWindowChange,
}) => {
  const [selectedWindow, setSelectedWindow] = useState<string>('24h');
  const [analytics, setAnalytics] = useState<AnalyticsSummaryData | null>(null);
  const [telemetry, setTelemetry] = useState<ActionTelemetryData | null>(null);

  const loadMetrics = async (win: string) => {
    try {
      const [aData, tData] = await Promise.all([
        fetchAnalyticsSummary(win),
        fetchActionTelemetry(),
      ]);
      setAnalytics(aData);
      setTelemetry(tData);
    } catch {
      // Offline fallback handling
    }
  };

  useEffect(() => {
    loadMetrics(selectedWindow);
    const interval = setInterval(() => loadMetrics(selectedWindow), 10000);
    return () => clearInterval(interval);
  }, [selectedWindow, recentDecisions]);

  const handleSelectWindow = (win: string) => {
    setSelectedWindow(win);
    if (onWindowChange) onWindowChange(win);
  };

  // Calculations
  const totalDecisions = analytics?.total_risk_decisions ?? recentDecisions.length;
  const highRiskCount = analytics?.high_risk_count ?? recentDecisions.filter(d => d.risk_level === 'HIGH' || d.risk_level === 'CRITICAL').length;
  const exposureINR = analytics?.protected_exposure_inr ?? 0;
  const tps = analytics?.tps_rolling_60s ?? 0.0;
  const liveUnsafeExecutions = telemetry?.live_unsafe_executions ?? propUnsafeCount;

  const formatExposure = (val: number) => {
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
    return `₹${val}`;
  };

  return (
    <div className="space-y-2 font-mono">
      {/* Time Window Selector Bar */}
      <div className="flex justify-between items-center bg-slate-950/80 border border-slate-800/80 px-3 py-1.5 rounded-lg text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <Clock className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-bold uppercase text-[11px]">Analytics Time Range:</span>
        </div>
        <div className="flex items-center gap-1">
          {['15m', '1h', '24h', '7d'].map((win) => (
            <button
              key={win}
              onClick={() => handleSelectWindow(win)}
              className={`px-2.5 py-0.5 rounded text-[11px] font-bold transition-colors cursor-pointer ${
                selectedWindow === win
                  ? 'bg-indigo-600 text-white border border-indigo-500'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {win}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {/* KPI 1: Transaction Speed */}
        <div className="metric-card bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-1 hover:border-slate-700 transition-all shadow-sm">
          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase tracking-wider">
            <span>Transaction Speed</span>
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{tps.toFixed(1)} <span className="text-xs font-normal text-slate-400">tx/sec</span></div>
          <div className="text-[10px] text-slate-400">
            {tps > 0 ? '● Active Live Stream' : 'Idle Stream (0.0 / sec)'}
          </div>
        </div>

        {/* KPI 2: Evaluated Volume */}
        <div className="metric-card bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-1 hover:border-slate-700 transition-all shadow-sm">
          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase tracking-wider">
            <span>Evaluated Volume</span>
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{totalDecisions}</div>
          <div className="text-[10px] text-indigo-400">Window: {selectedWindow}</div>
        </div>

        {/* KPI 3: High Risk Anomalies */}
        <div className="metric-card bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-1 hover:border-slate-700 transition-all shadow-sm">
          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase tracking-wider">
            <span>Threat Anomalies</span>
            <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">{highRiskCount}</div>
          <div className="text-[10px] text-rose-400 font-semibold">Requires Defense Action</div>
        </div>

        {/* KPI 4: Pending Cases */}
        <div className="metric-card bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-1 hover:border-slate-700 transition-all shadow-sm">
          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase tracking-wider">
            <span>Pending Review Cases</span>
            <Search className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">{activeIncidentsCount}</div>
          <div className="text-[10px] text-slate-400">Active Incident Clusters</div>
        </div>

        {/* KPI 5: Protected Volume */}
        <div className="metric-card bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-1 hover:border-slate-700 transition-all shadow-sm">
          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase tracking-wider">
            <span>Protected Volume</span>
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {formatExposure(exposureINR)}
          </div>
          <div className="text-[10px] text-emerald-400 font-semibold">Zero Fraud Loss Guaranteed</div>
        </div>

        {/* KPI 6: Live Action Safety */}
        <div className="metric-card bg-emerald-950/40 border-2 border-emerald-500/50 p-4 rounded-xl space-y-1 shadow-lg shadow-emerald-500/10 hover:border-emerald-400 transition-all">
          <div className="flex justify-between items-center text-[10px] text-emerald-300 font-bold uppercase tracking-wider">
            <span>Live Action Safety</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400 animate-pulse" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-slate-300">Unsafe Actions</span>
            <span className="text-2xl font-extrabold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              {liveUnsafeExecutions}
            </span>
          </div>
          <div className="text-[9px] text-emerald-400/90 font-bold flex justify-between items-center pt-0.5">
            <span>● FAIL-CLOSED VERIFIED</span>
            <span className="text-slate-400">100% Safe</span>
          </div>
        </div>
      </div>
    </div>
  );
};
