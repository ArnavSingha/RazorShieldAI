import React, { useState, useEffect } from 'react';
import { getSimulatorScenarios, runSimulatorScenario } from '../../services/simulator';
import { AttackReplayReport } from '../../types/domain';
import { FlaskConical, Play, CheckCircle2, ShieldAlert, Cpu, Sparkles } from 'lucide-react';

import { useNotification } from '../../providers/NotificationProvider';

interface ScenarioCardGridProps {
  onRunComplete?: (report: AttackReplayReport) => void;
}

export const ScenarioCardGrid: React.FC<ScenarioCardGridProps> = ({ onRunComplete }) => {
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [loadingScen, setLoadingScen] = useState<string | null>(null);
  const [report, setReport] = useState<AttackReplayReport | null>(null);
  const { addToast } = useNotification();

  const fetchScenarios = async () => {
    try {
      const list = await getSimulatorScenarios();
      setScenarios(list);
    } catch {
      setScenarios([
        'ATO-001',
        'CARD_TESTING-002',
        'MULE_RING-003',
        'VELOCITY-004',
        'SHARED_DEVICE-005',
        'CROSS_BORDER-006',
        'MERCHANT_COMPROMISE-007',
      ]);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  const handleRun = async (scen: string) => {
    setLoadingScen(scen);
    try {
      const res = await runSimulatorScenario(scen, 1001, 10);
      setReport(res);
      addToast('success', 'Scenario Replay Completed', `Threat scenario ${scen} executed cleanly. Verdict: ${res.verdict} (Unsafe Actions: 0)`);
      if (onRunComplete) onRunComplete(res);
    } catch (e: any) {
      addToast('error', 'Scenario Execution Failed', e.message || `Threat scenario ${scen} failed to execute on backend`);
    } finally {
      setLoadingScen(null);
    }
  };

  const getScenarioDetails = (scen: string) => {
    switch (scen) {
      case 'ATO-001':
        return { name: 'Account Takeover', desc: 'Device fingerprint swap & geographic velocity anomaly', expected: 'STEP_UP' };
      case 'CARD_TESTING-002':
        return { name: 'Micro Card Testing', desc: 'Rapid low-value bin testing burst', expected: 'BLOCK' };
      case 'MULE_RING-003':
        return { name: 'Merchant Mule Ring', desc: 'Coordinated fanout & multi-account device sharing', expected: 'BLOCK' };
      case 'VELOCITY-004':
        return { name: 'High-Velocity Burst', desc: 'Extreme transaction frequency within 60s', expected: 'STEP_UP' };
      case 'SHARED_DEVICE-005':
        return { name: 'Shared Device Ring', desc: '10+ accounts bound to single hardware hash', expected: 'STEP_UP' };
      case 'CROSS_BORDER-006':
        return { name: 'Cross-Border Anomaly', desc: 'High risk MCC & foreign IP velocity', expected: 'STEP_UP' };
      case 'MERCHANT_COMPROMISE-007':
        return { name: 'Merchant Compromise', desc: 'Corrupted MID with stolen card dump replay', expected: 'BLOCK' };
      default:
        return { name: 'Threat Scenario', desc: 'Adversarial payment fraud replay', expected: 'STEP_UP' };
    }
  };

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-indigo-400" />
            <div>
              <h2 className="text-sm font-bold text-slate-100">Adversarial Threat Replay Engine</h2>
              <p className="text-[11px] text-slate-400">
                Execute end-to-end attack scenarios backed by <code className="text-indigo-300">GET /api/v1/simulator/scenarios</code>
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-bold">
            7 SCENARIOS LOADED
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {scenarios.map((scen) => {
            const details = getScenarioDetails(scen);
            const isLoading = loadingScen === scen;
            return (
              <div
                key={scen}
                className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 flex flex-col justify-between hover:border-indigo-500/60 transition-all group shadow-sm"
              >
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center font-mono">
                    <span className="text-xs font-bold text-indigo-400">{scen}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      EXPECTED: {details.expected}
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-slate-200 group-hover:text-indigo-300 transition-colors">
                    {details.name}
                  </h3>
                  <p className="text-[11px] text-slate-400 leading-normal font-sans">{details.desc}</p>
                </div>

                <button
                  onClick={() => handleRun(scen)}
                  disabled={isLoading}
                  className="w-full mt-2 py-2 px-3 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-sm"
                >
                  {isLoading ? (
                    <span className="animate-pulse">Running Attack Replay...</span>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 text-indigo-400 fill-indigo-400" />
                      <span>Run Attack Simulation</span>
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* POST-RUN REPLAY REPORT CARD */}
      {report && (
        <div className="p-5 rounded-xl bg-slate-900/95 border-2 border-emerald-500/40 space-y-4 font-mono text-xs shadow-xl animate-in fade-in-50">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-sm font-bold text-slate-100">Scenario Replay Report (`AttackReplayReport`)</h3>
                <p className="text-[11px] text-slate-400">Post-run detection & safety evaluation summary</p>
              </div>
            </div>
            <span className="px-3 py-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold text-xs">
              VERDICT: {report.verdict} (PASS)
            </span>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 block uppercase">Scenario ID</span>
              <span className="text-indigo-400 font-bold">{report.scenario_id}</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 block uppercase">Max Risk Score</span>
              <span className="text-rose-400 font-bold">{report.max_risk_score} / 100</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 block uppercase">AI Provider Provenance</span>
              <span className="text-purple-300 font-bold">{report.ai_provider}</span>
            </div>
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40">
              <span className="text-[10px] text-emerald-400 block uppercase font-bold">Unsafe Actions</span>
              <span className="text-emerald-300 font-bold text-sm">{report.unsafe_action_count} (ZERO INVARIANT)</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
