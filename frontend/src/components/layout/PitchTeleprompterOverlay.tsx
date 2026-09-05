import React, { useState, useEffect } from 'react';
import { NavView } from './Sidebar';
import { Play, ChevronRight, ChevronLeft, X, Sparkles, Tv, Eye } from 'lucide-react';

interface PitchTeleprompterOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectView: (view: NavView) => void;
}

export interface TeleprompterStep {
  step: number;
  timeRange: string;
  targetView: NavView;
  title: string;
  badge: string;
  script: string[];
  actionPrompt: string;
}

export const PITCH_STEPS: TeleprompterStep[] = [
  {
    step: 1,
    timeRange: '0:00 – 0:35',
    targetView: 'command',
    title: '1. Problem Statement & Operations Overview',
    badge: 'COMMAND CENTER',
    actionPrompt: 'Keep mouse still. Point at Top KPIs & "Unsafe Actions: 0". Press Right Arrow (→) to continue.',
    script: [
      "Hi, I'm presenting RazorShield AI — a payment-risk operations system built for Track 02 (AI Risk Manager).",
      "The problem I'm solving is coordinated payment fraud. A suspicious payment is rarely obvious from a single field. The important signal can emerge from relationships between accounts, devices, IPs, payment instruments, merchants, transaction velocity and geography.",
      "RazorShield brings these signals together, investigates the resulting risk network, explains the evidence, and routes the final response through a deterministic control plane rather than allowing an AI model to directly execute a financial action.",
      "Let me show you the complete workflow."
    ]
  },
  {
    step: 2,
    timeRange: '0:35 – 1:15',
    targetView: 'simulator',
    title: '2. Real Attack Replay & Detection Pipeline',
    badge: 'ATTACK SIMULATOR',
    actionPrompt: 'Click MULE_RING-003 scenario card -> Click "Launch Scenario". Press Right Arrow (→).',
    script: [
      "I'll start with an attack replay so the system has an actual event to investigate. This is explicitly simulation data. It is separated from live payment traffic and cannot be mistaken for a real customer transaction.",
      "The event now enters the same risk pipeline used by the application.",
      "The deterministic signal layer evaluates transaction and behavioral anomalies. The ML layer provides an independent anomaly signal. And the graph engine looks beyond the individual transaction to identify relationships across entities.",
      "That's important because a transaction can look borderline in isolation while its surrounding network reveals coordinated abuse."
    ]
  },
  {
    step: 3,
    timeRange: '1:15 – 2:15',
    targetView: 'investigations',
    title: '3. Fraud Graph, Evidence Grounding & AI Investigator',
    badge: 'INVESTIGATIONS (MONEY SHOT 1)',
    actionPrompt: 'Click Fraud Graph node -> Click evidence badge (E-1001) -> Scroll to AI reasoning.',
    script: [
      "Now we move from detection to investigation. This is where RazorShield goes beyond a conventional fraud classifier. Instead of giving the analyst only a risk score, we expose the entities and relationships that contributed to the investigation.",
      "The graph connects the relevant payment entities and allows the analyst to move from an individual transaction to the surrounding fraud network. Selecting an entity opens its context rather than forcing the analyst to investigate blindly.",
      "The Why Flagged view decomposes the risk into evidence-backed factors. When I select an evidence item, the corresponding graph relationship is highlighted. This creates a traceable path from the risk decision back to underlying data.",
      "Only now do we involve the AI investigator. Gemini is used as an investigation and reasoning layer, not as the authority that executes payment actions. Every finding must reference evidence that exists in the investigation package. If the model produces an unknown or empty evidence reference, the output is rejected rather than silently rewritten."
    ]
  },
  {
    step: 4,
    timeRange: '2:15 – 2:50',
    targetView: 'policies',
    title: '4. AI Advisory vs Authoritative Control Plane',
    badge: 'POLICY DECISIONS',
    actionPrompt: 'Pause 2 seconds! Highlight banner: "AI IS ADVISORY • CONTROL PLANE IS AUTHORITATIVE".',
    script: [
      "Here is one of the most important architectural decisions in RazorShield.",
      "The AI recommendation and the policy decision are deliberately separated. The model can recommend an action based on its investigation, but the deterministic Policy Engine remains authoritative.",
      "The model cannot override the policy engine and cannot directly execute a financial action. This allows AI to contribute intelligence without giving an LLM uncontrolled financial authority."
    ]
  },
  {
    step: 5,
    timeRange: '2:50 – 3:35',
    targetView: 'actions',
    title: '5. Action Gateway & Human-in-the-Loop Approval',
    badge: 'ACTION GATEWAY',
    actionPrompt: 'Click "Execute Policy Response" -> Show Action Token modal -> Click "Confirm Execution".',
    script: [
      "Now we reach the action boundary. Nothing is automatically executed because an AI model recommended it.",
      "The Action Gateway evaluates the actor's capability, policy state, risk and required approval level. The analyst receives an explicit review before execution.",
      "The confirmation step exposes the target, risk, policy reason, AI recommendation, expected effect, actor and current token state before anything is executed. This is deliberately a human-in-the-loop boundary.",
      "Only after explicit confirmation does the Action Gateway execute the action."
    ]
  },
  {
    step: 6,
    timeRange: '3:35 – 4:05',
    targetView: 'audit',
    title: '6. Immutable SHA-256 Cryptographic Audit Ledger',
    badge: 'AUDIT TRAIL',
    actionPrompt: 'Point at Action Event, SHA-256 Hash Chain & "CHAIN VERIFIED ✓" status.',
    script: [
      "After execution, the decision lineage is recorded in the cryptographic audit trail.",
      "The analyst can reconstruct what happened, who authorized it, what policy allowed it and what action was executed.",
      "This gives the risk operation an auditable chain rather than an isolated decision record."
    ]
  },
  {
    step: 7,
    timeRange: '4:05 – 4:35',
    targetView: 'chaos',
    title: '7. Chaos Lab & Safe Fail-Closed Resilience',
    badge: 'CHAOS LAB (MONEY SHOT 2)',
    actionPrompt: 'Toggle LLM_SERVICE_OFFLINE -> ON -> Point to "FALLBACK ACTIVE" & "UNSAFE ACTIONS: 0".',
    script: [
      "Now let's test what happens when a dependency fails.",
      "I'll toggle LLM_SERVICE_OFFLINE to ON. Gemini is now unavailable.",
      "The system does not pretend that the AI is still healthy. The UI exposes the degraded state and the system falls back to deterministic controls.",
      "Most importantly, dependency failure does not create an unsafe execution path. Dependency failure must reduce capability, not reduce safety."
    ]
  },
  {
    step: 8,
    timeRange: '4:35 – 5:00',
    targetView: 'evaluation',
    title: '8. Held-Out Benchmark & Honest Trade-off',
    badge: 'BENCHMARKS',
    actionPrompt: 'Point to Recall vs FPR table -> Return to Command Center for final closing statement.',
    script: [
      "Finally, I don't want to claim that the system is good simply because the architecture looks good. RazorShield evaluates multiple detector configurations against an isolated 500-record held-out dataset containing 77 fraud and 423 benign records.",
      "The benchmark exposes the actual precision, recall and false-positive trade-offs rather than hiding them. For example, the rules-plus-ML configuration reaches 89.61 percent recall, but its false-positive rate is also high. The ML-only configuration has a much lower false-positive rate, but catches less fraud.",
      "RazorShield combines fraud detection, network investigation, grounded AI reasoning and a controlled action gateway into one risk-operations workflow.",
      "The goal isn't to make AI autonomous at any cost. The goal is to make fraud operations faster, more explainable and safer. Thank you."
    ]
  }
];

export const PitchTeleprompterOverlay: React.FC<PitchTeleprompterOverlayProps> = ({
  isOpen,
  onClose,
  onSelectView,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  // Default to Stealth Mode (NO modal box on screen)
  const [isStealthHidden, setIsStealthHidden] = useState<boolean>(true);

  const currentStep = PITCH_STEPS[currentStepIndex];

  useEffect(() => {
    if (isOpen && currentStep) {
      onSelectView(currentStep.targetView);
    }
  }, [currentStepIndex, isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        e.preventDefault();
        handleNext();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        handlePrev();
      } else if (e.key.toLowerCase() === 'h') {
        e.preventDefault();
        setIsStealthHidden((prev) => !prev);
      } else if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentStepIndex]);

  if (!isOpen) return null;

  const handleNext = () => {
    if (currentStepIndex < PITCH_STEPS.length - 1) {
      const nextIdx = currentStepIndex + 1;
      setCurrentStepIndex(nextIdx);
      onSelectView(PITCH_STEPS[nextIdx].targetView);
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      const prevIdx = currentStepIndex - 1;
      setCurrentStepIndex(prevIdx);
      onSelectView(PITCH_STEPS[prevIdx].targetView);
    }
  };

  // Default Stealth Spotlight Bar (Clean recording with zero script modal)
  if (isStealthHidden) {
    return (
      <div className="fixed bottom-3 right-3 z-50 font-sans select-none pointer-events-auto">
        <div className="bg-slate-950/95 border-2 border-indigo-500/80 rounded-xl shadow-2xl p-2.5 flex items-center gap-3 backdrop-blur-xl animate-in slide-in-from-bottom-2">
          <span className="text-[11px] font-mono font-bold text-indigo-300 px-2 py-0.5 rounded bg-indigo-950 border border-indigo-800 shrink-0">
            STEP {currentStep.step}/8
          </span>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
              <span>{currentStep.title}</span>
            </span>
            <span className="text-[10px] text-slate-400 font-mono">{currentStep.actionPrompt}</span>
          </div>

          <div className="flex items-center gap-1 border-l border-slate-800 pl-2 shrink-0">
            <button
              onClick={handlePrev}
              disabled={currentStepIndex === 0}
              className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 disabled:opacity-30 cursor-pointer"
              title="Previous Step (←)"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={handleNext}
              disabled={currentStepIndex === PITCH_STEPS.length - 1}
              className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-1 cursor-pointer shadow-md shadow-indigo-600/30"
              title="Next Step (→ or Right Arrow)"
            >
              <span>Next (→)</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setIsStealthHidden(false)}
              className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 cursor-pointer"
              title="Show Script Text Box (H)"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 cursor-pointer"
              title="Exit Recording Mode"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Full Script Teleprompter Mode (Optional if opened via Eye icon)
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 font-sans select-none pointer-events-none">
      <div className="max-w-5xl mx-auto bg-slate-950/95 border-2 border-indigo-500/60 rounded-2xl shadow-2xl shadow-indigo-500/20 backdrop-blur-xl p-5 pointer-events-auto transition-all animate-in slide-in-from-bottom-6">
        {/* Header Bar */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800 text-xs">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-indigo-600 text-white font-bold tracking-wider text-[11px] uppercase shadow-sm">
              <Tv className="w-3.5 h-3.5 text-indigo-200" />
              <span>STEP {currentStep.step} OF 8</span>
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono text-[11px] font-bold border border-slate-700">
              ⏱ {currentStep.timeRange}
            </span>
            <h3 className="font-bold text-slate-100 text-sm tracking-tight">{currentStep.title}</h3>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsStealthHidden(true)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all cursor-pointer"
            >
              <span>Back to Stealth Mode</span>
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Script Content */}
        <div className="p-4 bg-slate-900/90 rounded-xl border border-slate-800 space-y-2.5 max-h-44 overflow-y-auto custom-scrollbar">
          {currentStep.script.map((paragraph, idx) => (
            <p key={idx} className="text-sm md:text-base font-medium text-slate-100 leading-relaxed tracking-wide">
              {paragraph}
            </p>
          ))}
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-800/80">
          <button
            onClick={handlePrev}
            disabled={currentStepIndex === 0}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 disabled:opacity-30 cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4 text-slate-400" />
            <span>Previous Step</span>
          </button>
          <button
            onClick={handleNext}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold border border-indigo-400 cursor-pointer"
          >
            <span>Next Step (→)</span>
            <ChevronRight className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
};
