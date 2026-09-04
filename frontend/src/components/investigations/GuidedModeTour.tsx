import React, { useState } from 'react';
import { HelpCircle, ChevronRight, ChevronLeft, X, ShieldAlert, CheckCircle2, FileText, Lock } from 'lucide-react';

interface GuidedModeTourProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectStep?: (step: number) => void;
  caseDetails?: {
    title: string;
    amount: string;
    riskScore: number;
    reason: string;
    aiRec: string;
    policyRec: string;
  };
}

export const GuidedModeTour: React.FC<GuidedModeTourProps> = ({
  isOpen,
  onClose,
  caseDetails = {
    title: 'Suspicious Payment Network (MULE_RING-003)',
    amount: '₹3,10,000',
    riskScore: 96,
    reason: '4 accounts are sharing the same physical device fingerprint (dev_shared_ring_09) within 24 hours.',
    aiRec: 'BLOCK PAYMENT',
    policyRec: 'STEP-UP VERIFICATION',
  },
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);

  if (!isOpen) return null;

  const steps = [
    {
      num: 1,
      title: 'Step 1: What Happened?',
      icon: <ShieldAlert className="w-5 h-5 text-rose-400" />,
      content: (
        <div className="space-y-3">
          <p className="text-sm text-slate-200">
            A payment transaction totaling <strong className="text-white font-bold">{caseDetails.amount}</strong> was flagged because multiple accounts showed coordinated activity.
          </p>
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-xs text-slate-400 font-semibold uppercase">Flagged Entity</span>
            <p className="text-sm text-indigo-300 font-bold">{caseDetails.title}</p>
          </div>
        </div>
      ),
    },
    {
      num: 2,
      title: 'Step 2: Why Is It Suspicious?',
      icon: <FileText className="w-5 h-5 text-amber-400" />,
      content: (
        <div className="space-y-3">
          <p className="text-sm text-slate-200">
            {caseDetails.reason}
          </p>
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Risk Assessment</span>
              <span className="text-rose-400 font-bold">{caseDetails.riskScore}/100 (Very High)</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div className="bg-rose-500 h-full rounded-full" style={{ width: `${caseDetails.riskScore}%` }}></div>
            </div>
          </div>
        </div>
      ),
    },
    {
      num: 3,
      title: 'Step 3: What Does RazorShield Recommend?',
      icon: <HelpCircle className="w-5 h-5 text-indigo-400" />,
      content: (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-rose-500/10 rounded-lg border border-rose-500/30 space-y-1">
              <span className="text-[11px] text-rose-400 uppercase font-bold">AI Assistant</span>
              <p className="text-xs text-slate-100 font-bold">{caseDetails.aiRec}</p>
              <p className="text-[10px] text-slate-400">96% confidence based on network graph evidence</p>
            </div>
            <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/30 space-y-1">
              <span className="text-[11px] text-amber-400 uppercase font-bold">Company Policy</span>
              <p className="text-xs text-slate-100 font-bold">{caseDetails.policyRec}</p>
              <p className="text-[10px] text-slate-400">Requires step-up OTP due to customer tenure</p>
            </div>
          </div>
        </div>
      ),
    },
    {
      num: 4,
      title: 'Step 4: Review & Take Action',
      icon: <Lock className="w-5 h-5 text-emerald-400" />,
      content: (
        <div className="space-y-3">
          <p className="text-sm text-slate-200">
            Review the evidence summary and authorize the appropriate response. All actions are cryptographically signed and tracked for audit compliance.
          </p>
          <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/30 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="text-xs text-emerald-300 font-medium">✓ Decision state is current & authorized for execution</span>
          </div>
        </div>
      ),
    },
  ];

  const currentStepData = steps[currentStep - 1];

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-indigo-500/40 rounded-2xl shadow-2xl shadow-indigo-500/10 overflow-hidden font-sans">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/30">
              {currentStepData.icon}
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">{currentStepData.title}</h3>
              <p className="text-xs text-slate-400">Guided Analyst Walkthrough (Step {currentStep} of 4)</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">{currentStepData.content}</div>

        {/* Footer Navigation */}
        <div className="px-6 py-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
          <button
            onClick={() => setCurrentStep((s) => Math.max(1, s - 1))}
            disabled={currentStep === 1}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
              currentStep === 1
                ? 'opacity-40 cursor-not-allowed text-slate-500 border-slate-800'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700 cursor-pointer'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          {/* Stepper Dots */}
          <div className="flex items-center gap-1.5">
            {steps.map((s) => (
              <div
                key={s.num}
                onClick={() => setCurrentStep(s.num)}
                className={`w-2.5 h-2.5 rounded-full transition-all cursor-pointer ${
                  currentStep === s.num
                    ? 'bg-indigo-500 w-6'
                    : s.num < currentStep
                    ? 'bg-indigo-400/50'
                    : 'bg-slate-800'
                }`}
              />
            ))}
          </div>

          {currentStep < 4 ? (
            <button
              onClick={() => setCurrentStep((s) => Math.min(4, s + 1))}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold border border-indigo-400 transition-colors cursor-pointer"
            >
              <span>Next</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={onClose}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold border border-emerald-400 transition-colors cursor-pointer"
            >
              <span>Done</span>
              <CheckCircle2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
