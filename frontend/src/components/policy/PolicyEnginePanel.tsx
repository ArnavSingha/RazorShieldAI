import React from 'react';
import { PolicyDecision, AgentInvestigationResult } from '../../types/domain';
import { ArrowRightLeft, Sliders } from 'lucide-react';

interface PolicyEnginePanelProps {
  policyDecision: PolicyDecision | null;
  agentResult: AgentInvestigationResult | null;
}

export const PolicyEnginePanel: React.FC<PolicyEnginePanelProps> = ({ policyDecision, agentResult }) => {
  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 font-mono text-xs">
      {/* Central Statement */}
      <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-500/40 text-center space-y-1">
        <p className="text-xs font-mono font-bold tracking-wider text-indigo-300 uppercase">
          AI IS ADVISORY • CONTROL PLANE IS AUTHORITATIVE
        </p>
        <p className="text-[11px] text-slate-400 font-sans">
          Deterministic Policy Engine holds 100% authoritative override power over AI recommendations.
        </p>
      </div>

      {/* Side by Side Comparison Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Left Column: AI Investigator */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
            <span className="text-xs font-bold text-purple-400">AI INVESTIGATOR</span>
            <span className="text-[10px] text-slate-500">ADVISORY</span>
          </div>

          {agentResult ? (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Recommendation:</span>
                <span className="text-rose-400 font-bold px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30">
                  {agentResult.recommended_action}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Confidence:</span>
                <span className="text-indigo-400 font-bold">
                  {(agentResult as any).confidence_score !== undefined
                    ? ((agentResult as any).confidence_score <= 1.0 ? Math.round((agentResult as any).confidence_score * 100) : Math.round((agentResult as any).confidence_score))
                    : ((agentResult as any).confidence !== undefined ? ((agentResult as any).confidence <= 1.0 ? Math.round((agentResult as any).confidence * 100) : Math.round((agentResult as any).confidence)) : 70)}%
                </span>
              </div>
              <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-900 leading-relaxed font-sans truncate">
                {agentResult.agent_reasoning}
              </div>
            </div>
          ) : (
            <div className="p-4 text-center text-slate-500 italic font-sans">
              No AI recommendation generated yet.
            </div>
          )}
        </div>

        {/* Right Column: Deterministic Policy Engine */}
        <div className="p-4 rounded-xl bg-slate-950 border-2 border-amber-500/40 space-y-3 shadow-lg shadow-amber-500/5">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
            <span className="text-xs font-bold text-amber-400">DETERMINISTIC POLICY</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
              AUTHORITATIVE
            </span>
          </div>

          {policyDecision ? (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Final Policy Action:</span>
                <span className="text-amber-400 font-bold px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30">
                  {policyDecision.final_action}
                </span>
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Policy Version:</span>
                <span className="text-slate-200">{policyDecision.policy_version}</span>
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">AI Override Status:</span>
                <span className={policyDecision.override_active ? "text-amber-400 font-bold" : "text-emerald-400 font-bold"}>
                  {policyDecision.override_active ? "YES (OVERRIDDEN)" : "NO OVERRIDE (ALIGNED)"}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-4 text-center text-slate-500 italic font-sans">
              Awaiting analyst action authorization.
            </div>
          )}
        </div>
      </div>

      {/* Override Reason Codes */}
      {policyDecision?.override_active && policyDecision.override_reason_codes && (
        <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-2 text-xs">
          <div className="flex items-center gap-2 text-amber-400 font-bold">
            <ArrowRightLeft className="w-4 h-4" />
            <span>Deterministic Policy Override Reason Codes</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {policyDecision.override_reason_codes.map((code) => (
              <span key={code} className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[11px] font-bold">
                {code}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
