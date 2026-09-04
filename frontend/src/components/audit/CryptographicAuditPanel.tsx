import React, { useState } from 'react';
import { AuditVerificationData } from '../../types/domain';
import { History, CheckCircle2, AlertOctagon, RefreshCw } from 'lucide-react';
import { verifyAuditLedger } from '../../services/audit';

interface CryptographicAuditPanelProps {
  auditData: AuditVerificationData | null;
}

export const CryptographicAuditPanel: React.FC<CryptographicAuditPanelProps> = ({ auditData: initialAuditData }) => {
  const [auditData, setAuditData] = useState<AuditVerificationData | null>(initialAuditData);
  const [verifying, setVerifying] = useState<boolean>(false);

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await verifyAuditLedger();
      setAuditData(res);
    } catch {
      setAuditData(null);
    } finally {
      setVerifying(false);
    }
  };

  const isVerified = auditData?.ledger_valid;
  const chainLength = auditData?.verified_chain_length ?? 0;
  const tipHash = auditData?.tip_hash || 'Unverified Merkle Tip Hash';
  const storageMode = auditData?.storage_mode || 'SHA256_LEDGER';

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 font-mono text-xs">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-100">Cryptographic SHA-256 Chained Audit Trail</h2>
            <p className="text-[11px] text-slate-400">
              Tamper-evident audit lineage verified via <code className="text-indigo-300">GET /api/v1/audit/verify</code>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleVerify}
            disabled={verifying}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-indigo-400 ${verifying ? 'animate-spin' : ''}`} />
            <span>Verify Merkle Chain</span>
          </button>

          {/* VERIFIED BADGE */}
          {auditData === null ? (
            <span className="px-3 py-1 rounded-md font-bold bg-slate-800 text-slate-400 border border-slate-700 text-[11px]">
              UNVERIFIED
            </span>
          ) : isVerified ? (
            <span className="px-3 py-1 rounded-md font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5 shadow-sm text-[11px]">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>CHAIN VERIFIED ✓</span>
            </span>
          ) : (
            <span className="px-3 py-1 rounded-md font-bold bg-rose-500/15 text-rose-300 border border-rose-500/40 flex items-center gap-1.5 text-[11px]">
              <AlertOctagon className="w-4 h-4 text-rose-400" />
              <span>TAMPER DETECTED ❌</span>
            </span>
          )}
        </div>
      </div>

      {/* Audit Chain Metadata */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-500 block uppercase">Verified Chain Length</span>
          <span className="text-lg font-bold text-indigo-400">{chainLength} Blocks</span>
        </div>
        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1 col-span-2">
          <div className="flex justify-between items-center text-[10px] text-slate-500 uppercase">
            <span>Latest Merkle Tip Hash</span>
            <span className="text-slate-400 font-bold">{storageMode}</span>
          </div>
          <span className="text-slate-300 text-[10px] font-mono block truncate" title={tipHash}>
            {tipHash}
          </span>
        </div>
      </div>
    </div>
  );
};
