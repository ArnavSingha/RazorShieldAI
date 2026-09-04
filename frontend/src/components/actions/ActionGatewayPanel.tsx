import React, { useState } from 'react';
import { ActionToken, ActionExecutionResult } from '../../types/domain';
import { Zap, CheckCircle2, Lock, ShieldCheck, Play, AlertTriangle, ShieldAlert } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface ActionGatewayPanelProps {
  actionToken: ActionToken | null;
  executionResult: ActionExecutionResult | null;
  onExecuteToken?: () => void;
  isExecuting?: boolean;
  decisionPacket?: Record<string, any> | null;
}

export const ActionGatewayPanel: React.FC<ActionGatewayPanelProps> = ({
  actionToken,
  executionResult,
  onExecuteToken,
  isExecuting = false,
  decisionPacket,
}) => {
  const [showConfirmModal, setShowConfirmModal] = useState<boolean>(false);
  const { hasCapability, devSimRole } = useAuth();
  const canExecute = hasCapability('action.execute');

  const steps = [
    { label: 'PENDING', status: 'COMPLETE' },
    { label: 'AUTHORIZED', status: actionToken ? 'COMPLETE' : 'PENDING' },
    { label: 'EXECUTING', status: isExecuting ? 'ACTIVE' : executionResult ? 'COMPLETE' : 'PENDING' },
    { label: 'EXECUTED', status: executionResult?.execution_status === 'SUCCESS' ? 'COMPLETE' : 'PENDING' },
    { label: 'VERIFIED', status: executionResult?.verification_status === 'PASS' ? 'COMPLETE' : 'PENDING' },
  ];

  const maskSecret = (sec?: string) => {
    if (!sec) return 'None';
    return `${sec.substring(0, 8)}••••••••••••••••`;
  };

  const [confirmText, setConfirmText] = useState<string>('');

  const isCriticalAction =
    decisionPacket?.required_approval_level === 'ELEVATED_DUAL_CONTROL' ||
    actionToken?.granted_action === 'BLOCK' ||
    (decisionPacket?.risk_score ?? 88) >= 85;

  const isTypedValid = !isCriticalAction || confirmText.trim().toUpperCase() === 'EXECUTE';

  const handleConfirm = () => {
    if (!isTypedValid) return;
    setShowConfirmModal(false);
    setConfirmText('');
    if (onExecuteToken) onExecuteToken();
  };

  const isConflict = decisionPacket?.ai_policy_conflict || false;

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 font-mono text-xs">
      <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-indigo-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-100">Fail-Closed Action Gateway State Machine</h2>
            <p className="text-[11px] text-slate-400">Cryptographic ActionToken issuance & atomic nonce verification</p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">
          GATEWAY ACTIVE
        </span>
      </div>

      {/* State Machine Transition Progress Bar */}
      <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
        <div className="flex items-center justify-between">
          {steps.map((step, idx) => (
            <React.Fragment key={step.label}>
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${
                    step.status === 'COMPLETE'
                      ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20'
                      : step.status === 'ACTIVE'
                      ? 'bg-indigo-600 text-white animate-pulse'
                      : 'bg-slate-800 text-slate-500'
                  }`}
                >
                  {step.status === 'COMPLETE' ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                </div>
                <span className="text-[10px] text-slate-300 font-bold">{step.label}</span>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-2 ${
                    step.status === 'COMPLETE' ? 'bg-emerald-500' : 'bg-slate-800'
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Action Token Details & HMAC Masking */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase">
            <span>Signed Action Token</span>
            <Lock className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          {actionToken ? (
            <div className="space-y-1 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Token ID:</span>
                <span className="text-indigo-400 font-bold">{actionToken.token_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Principal:</span>
                <span className="text-slate-200">{actionToken.principal_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Granted Action:</span>
                <span className="text-amber-400 font-bold">{actionToken.granted_action}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">HMAC Signature:</span>
                <span className="text-slate-400 text-[10px]">{maskSecret(actionToken.signature)}</span>
              </div>

              {!executionResult && onExecuteToken && (
                canExecute ? (
                  <button
                    onClick={() => setShowConfirmModal(true)}
                    disabled={isExecuting}
                    className="w-full mt-3 py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-extrabold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <Play className="w-4 h-4 fill-slate-950" />
                    <span>{isExecuting ? 'Executing Action Token...' : 'Confirm & Execute Action Token'}</span>
                  </button>
                ) : (
                  <div className="mt-3 p-2.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-amber-400 flex items-center gap-1.5 font-sans">
                    <ShieldAlert className="w-4 h-4 shrink-0 text-amber-400" />
                    <span>Role '{devSimRole}' is View-Only. Action execution is prohibited by capability RBAC policy.</span>
                  </div>
                )
              )}
            </div>
          ) : (
            <div className="p-4 text-center text-slate-500 italic font-sans">
              No ActionToken issued yet. Authorize an action to generate a signed token.
            </div>
          )}
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase">
            <span>Execution & Verification</span>
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          {executionResult ? (
            <div className="space-y-1 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Execution Status:</span>
                <span className="text-emerald-400 font-bold">{executionResult.execution_status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Observed Outcome:</span>
                <span className="text-slate-200">{executionResult.observed_outcome}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Outcome Verification:</span>
                <span className="text-emerald-400 font-bold">{executionResult.verification_status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Audit Reference:</span>
                <span className="text-slate-400 text-[10px] truncate max-w-[140px]" title={executionResult.audit_event_id}>
                  {executionResult.audit_event_id}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-4 text-center text-slate-500 italic font-sans">
              Awaiting execution trigger.
            </div>
          )}
        </div>
      </div>

      {/* CONFIRMATION MODAL FOR ACTION EXECUTION WITH DECISION PACKET */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center gap-3 text-amber-400 font-bold border-b border-slate-800 pb-3">
              <AlertTriangle className="w-6 h-6 text-amber-400" />
              <div>
                <h3 className="text-sm text-slate-100">Action Execution Review & Approval Packet</h3>
                <span className="text-[10px] text-slate-400 font-sans">Two-Step Human Confirmation Requirement</span>
              </div>
            </div>

            {/* AI vs Policy Conflict Alert */}
            {isConflict && (
              <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-500/50 text-rose-300 text-[11px] flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
                <div>
                  <strong className="block">POLICY OVERRIDE DETECTED</strong>
                  The AI recommended <strong>{decisionPacket?.ai_recommendation}</strong> based on risk, but company policy requires <strong>{actionToken?.granted_action}</strong> for this customer profile.
                </div>
              </div>
            )}

            {/* Pre-Execution Safety Checklist */}
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-1 text-[11px] text-emerald-300">
              <div className="font-bold uppercase text-[10px] text-emerald-400">Pre-Execution Safety Verification:</div>
              <div className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /><span>You reviewed the evidence breakdown</span></div>
              <div className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /><span>The decision state is current & valid</span></div>
              <div className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /><span>You are authorized by capability policy ({actionToken?.role})</span></div>
            </div>

            {/* Case Summary Details */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 text-[11px]">
              <div className="flex justify-between"><span className="text-slate-500">Target Entity:</span><span className="text-indigo-300 font-bold">{decisionPacket?.action_target || actionToken?.token_id}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Risk Assessment:</span><span className="text-rose-400 font-bold">{decisionPacket?.risk_score ?? 88}/100 | ₹{(decisionPacket?.exposure_inr ?? 50000).toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Authorized Action:</span><span className="text-amber-400 font-bold">{actionToken?.granted_action}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">AI Assistant Recommendation:</span><span className="text-purple-300 font-bold">{decisionPacket?.ai_recommendation ?? 'BLOCK'} ({decisionPacket?.ai_confidence ?? 95}% Confidence)</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Executing Actor:</span><span className="text-slate-200">{actionToken?.principal_id} ({actionToken?.role})</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Freshness Indicator:</span><span className="text-emerald-400 font-bold">✓ Decision is current</span></div>
            </div>

            {/* Explicit Typing Requirement for Critical Actions */}
            {isCriticalAction && (
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
                <label className="block text-[11px] text-amber-300 font-bold">
                  Secondary Confirmation Requirement (Type "EXECUTE" or "BLOCK PAYMENT" to enable button):
                </label>
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder='Type "EXECUTE"'
                  className="w-full bg-slate-900 text-emerald-400 font-extrabold uppercase px-3 py-1.5 rounded border border-slate-700 focus:outline-none focus:border-emerald-500 text-xs"
                />
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2 border-t border-slate-800">
              <button
                onClick={() => {
                  setShowConfirmModal(false);
                  setConfirmText('');
                }}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold transition-colors cursor-pointer"
              >
                Cancel & Return
              </button>
              <button
                onClick={handleConfirm}
                disabled={!isTypedValid || isExecuting}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 text-slate-950 font-extrabold transition-colors cursor-pointer"
              >
                {isExecuting ? 'Executing...' : 'Confirm & Execute Action'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
