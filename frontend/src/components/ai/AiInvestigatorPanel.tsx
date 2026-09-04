import React from 'react';
import { AgentInvestigationResult } from '../../types/domain';
import { BrainCircuit, Sparkles, AlertOctagon, Play } from 'lucide-react';

interface AiInvestigatorPanelProps {
  agentResult: AgentInvestigationResult | null;
  onRunAgent?: () => void;
}

export const AiInvestigatorPanel: React.FC<AiInvestigatorPanelProps> = ({ agentResult, onRunAgent }) => {
  if (!agentResult) {
    return (
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 font-mono text-xs">
        <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-purple-400" />
            <div>
              <h2 className="text-sm font-bold text-slate-100">Gemini Autonomous Investigator</h2>
              <p className="text-[11px] text-slate-400">AI reasoning trace & grounded claim verification</p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded text-[10px] bg-slate-800 text-slate-400 border border-slate-700">
            AWAITING RUN
          </span>
        </div>

        <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-3">
          <p className="text-slate-400 leading-relaxed font-sans text-xs">
            No agent investigation has been run for this target yet. Click below to execute Gemini 3.6 Flash reasoning over the multi-hop fraud graph and evidence ledger.
          </p>
          {onRunAgent && (
            <button
              onClick={onRunAgent}
              className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold inline-flex items-center gap-2 transition-colors cursor-pointer"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>Run Gemini AI Investigation</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  const isFallback = agentResult.execution_mode === 'DETERMINISTIC_FALLBACK' || agentResult.ai_provider === 'DETERMINISTIC_FALLBACK';

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 font-mono text-xs">
      {/* Header with EXPLICIT PROVENANCE BADGE */}
      <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-purple-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-100">Gemini Autonomous Investigator</h2>
            <p className="text-[11px] text-slate-400">AI reasoning trace & grounded claim verification</p>
          </div>
        </div>

        {/* PROVENANCE BADGE - NEVER IMPLY GEMINI WHEN FALLBACK WAS USED */}
        {isFallback ? (
          <span className="px-3 py-1 rounded-md text-xs font-bold bg-amber-500/15 text-amber-300 border border-amber-500/40 flex items-center gap-1.5 shadow-sm">
            <AlertOctagon className="w-3.5 h-3.5 text-amber-400" />
            <span>DETERMINISTIC FALLBACK ACTIVE</span>
          </span>
        ) : (
          <span className="px-3 py-1 rounded-md text-xs font-bold bg-purple-500/15 text-purple-300 border border-purple-500/40 flex items-center gap-1.5 shadow-sm shadow-purple-500/10">
            <Sparkles className="w-3.5 h-3.5 text-purple-400 animate-pulse" />
            <span>LIVE GEMINI 3.6 FLASH</span>
          </span>
        )}
      </div>

      {/* Model Metadata Bar */}
      <div className="grid grid-cols-4 gap-3">
        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
          <span className="text-[10px] text-slate-500 block uppercase">Provider & Model</span>
          <span className="text-purple-300 font-bold truncate block">{agentResult.model_name}</span>
        </div>
        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
          <span className="text-[10px] text-slate-500 block uppercase">Confidence</span>
          <span className="text-indigo-400 font-bold">
            {(agentResult as any).confidence_score !== undefined
              ? ((agentResult as any).confidence_score <= 1.0 ? Math.round((agentResult as any).confidence_score * 100) : Math.round((agentResult as any).confidence_score))
              : ((agentResult as any).confidence !== undefined ? ((agentResult as any).confidence <= 1.0 ? Math.round((agentResult as any).confidence * 100) : Math.round((agentResult as any).confidence)) : 70)}%
          </span>
        </div>
        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
          <span className="text-[10px] text-slate-500 block uppercase">Recommendation</span>
          <span className="text-rose-400 font-bold">{agentResult.recommended_action}</span>
        </div>
        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
          <span className="text-[10px] text-slate-500 block uppercase">Latency & Tokens</span>
          <span className="text-slate-300 text-[11px]">
            {agentResult.resource_usage?.latency_ms ?? 0}ms • {agentResult.resource_usage?.tokens_used ?? 0} tok
          </span>
        </div>
      </div>

      {/* Agent Structured Reasoning */}
      <div className="space-y-2">
        <h3 className="text-[10px] font-bold text-slate-300 uppercase">Agent Reasoning Log</h3>
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-sans text-slate-200 leading-relaxed">
          {agentResult.agent_reasoning}
        </div>
      </div>

      {/* Grounded Evidence References & Counter Signals */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase">Grounded Evidence IDs</h4>
          <div className="flex flex-wrap gap-1.5">
            {(agentResult.grounded_evidence_ids && agentResult.grounded_evidence_ids.length > 0) ? (
              agentResult.grounded_evidence_ids.map((id) => (
                <span key={id} className="px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-[11px] font-bold">
                  {id}
                </span>
              ))
            ) : (
              <span className="text-slate-500 italic text-[11px]">None referenced</span>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase">Counter-Signals Considered</h4>
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 leading-relaxed font-sans">
            {(agentResult.counter_signals || []).join(' • ') || 'None observed'}
          </div>
        </div>
      </div>
    </div>
  );
};
