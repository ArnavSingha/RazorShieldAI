import React from 'react';
import { EvidenceItem } from '../../types/domain';
import { FileCheck2, ExternalLink } from 'lucide-react';

interface EvidenceExplorerProps {
  evidenceItems: EvidenceItem[];
  selectedEvidenceId?: string | null;
  onSelectEvidence?: (evidenceId: string) => void;
}

export const EvidenceExplorer: React.FC<EvidenceExplorerProps> = ({
  evidenceItems,
  selectedEvidenceId,
  onSelectEvidence,
}) => {
  const itemsToRender: EvidenceItem[] = evidenceItems || [];

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 font-mono text-xs">
      <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-indigo-400" />
            <span>Grounded Evidence Explorer</span>
          </h2>
          <p className="text-[11px] text-slate-400">
            Cryptographically grounded evidence snapshot powering agent reasoning
          </p>
        </div>
        <span className="text-[10px] px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-bold">
          {itemsToRender.length} EVIDENCE ITEMS
        </span>
      </div>

      {itemsToRender.length === 0 ? (
        <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 text-center text-slate-400 font-sans leading-relaxed">
          No grounded evidence items generated for this target yet. Ingest suspicious events or select an active threat cluster to explore evidence claims.
        </div>
      ) : (
        <div className="space-y-3">
          {itemsToRender.map((item) => {
            const isSelected = selectedEvidenceId === item.evidence_id;
            return (
              <div
                key={item.evidence_id}
                onClick={() => onSelectEvidence?.(item.evidence_id)}
                className={`p-4 rounded-xl bg-slate-950 border transition-all cursor-pointer space-y-2.5 ${
                  isSelected
                    ? 'border-indigo-500 shadow-md shadow-indigo-500/10'
                    : 'border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-2 py-0.5 rounded bg-indigo-600/20 text-indigo-300 font-bold border border-indigo-500/40">
                      {item.evidence_id}
                    </span>
                    <span className="text-slate-300 font-bold">{item.evidence_type}</span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px]">
                    <span className="text-slate-500">{item.freshness || 'Recent'}</span>
                    <span className="text-emerald-400 font-bold">{item.confidence}% Confidence</span>
                  </div>
                </div>

                <p className="text-xs text-slate-200 leading-relaxed font-sans">{item.claim}</p>

                <div className="flex justify-between items-center pt-2 border-t border-slate-900 text-[10px] text-slate-400">
                  <div>
                    <span className="text-slate-500 mr-1">Source Entities:</span>
                    <span className="text-indigo-300">{item.source_entities?.join(', ')}</span>
                  </div>
                  <div className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300">
                    <span>Highlight Graph Nodes</span>
                    <ExternalLink className="w-3 h-3" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
