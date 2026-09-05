import React, { useState, useEffect } from 'react';
import { RefreshCw, Clock, AlertTriangle, ShieldCheck, Wifi, UserCheck, HelpCircle } from 'lucide-react';
import { SystemStatusData } from '../../types/domain';
import { useAuth, UserRole } from '../../context/AuthContext';
import { realtimeStream, ConnectionState } from '../../services/sse';
import { GuidedModeTour } from '../investigations/GuidedModeTour';

interface TopBarProps {
  activeView: string;
  systemStatus: SystemStatusData | null;
  onRefresh?: () => void;
  onOpenCommandPalette?: () => void;
  onOpenPitchTeleprompter?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ activeView, systemStatus, onRefresh, onOpenCommandPalette, onOpenPitchTeleprompter }) => {
  const [timeStr, setTimeStr] = useState<string>('');
  const [connState, setConnState] = useState<ConnectionState>('CONNECTED');
  const [latencyMs, setLatencyMs] = useState<number>(124);
  const [showGuidedTour, setShowGuidedTour] = useState<boolean>(false);
  const { user, devSimRole, setDevSimRole } = useAuth();


  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTimeStr(now.toISOString().substring(11, 19) + ' UTC');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const unsubscribe = realtimeStream.subscribeState((st, lat) => {
      setConnState(st);
      if (lat) setLatencyMs(lat);
    });
    return unsubscribe;
  }, []);

  const getViewBreadcrumb = (view: string) => {
    switch (view) {
      case 'work-queue': return 'OPERATIONS / Analyst Work Queue';
      case 'command': return 'OPERATIONS / Command Center';
      case 'transactions': return 'OPERATIONS / Live Transactions';
      case 'investigations': return 'OPERATIONS / Case Summary & Story';
      case 'graph': return 'INTELLIGENCE / Fraud Graph Canvas';
      case 'ai': return 'INTELLIGENCE / AI Investigator';
      case 'evidence': return 'INTELLIGENCE / Evidence Explorer';
      case 'policies': return 'CONTROL PLANE / Policy Decisions';
      case 'actions': return 'CONTROL PLANE / Action Gateway';
      case 'audit': return 'CONTROL PLANE / Cryptographic Audit';
      case 'simulator': return 'RESILIENCE / Threat Simulator';
      case 'chaos': return 'RESILIENCE / Chaos Lab';
      case 'evaluation': return 'EVALUATION / 3-Track Benchmarks';
      default: return 'RAZORSHIELD / Console';
    }
  };

  const isUnreachable = systemStatus === null || connState === 'OFFLINE';
  const isDegraded = systemStatus?.degraded_mode || (systemStatus?.active_faults && systemStatus.active_faults.length > 0) || connState === 'DEGRADED';

  const renderConnectionBadge = () => {
    if (connState === 'OFFLINE' || isUnreachable) {
      return (
        <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/40 flex items-center gap-1.5 font-bold">
          <Wifi className="w-3 h-3 text-rose-400" />
          <span>🔴 OFFLINE · Backend unreachable</span>
        </span>
      );
    }
    if (connState === 'RECONNECTING') {
      return (
        <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/40 flex items-center gap-1.5 animate-pulse font-bold">
          <Wifi className="w-3 h-3 text-amber-400" />
          <span>◐ RECONNECTING · Retrying stream</span>
        </span>
      );
    }
    if (isDegraded) {
      return (
        <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/40 flex items-center gap-1.5 font-bold">
          <AlertTriangle className="w-3 h-3 text-amber-400" />
          <span>⚠ DEGRADED · Risk Engine offline</span>
        </span>
      );
    }
    return (
      <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 font-bold">
        <ShieldCheck className="w-3 h-3 text-emerald-400" />
        <span>● LIVE · {latencyMs}ms</span>
      </span>
    );
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800/80 px-6 py-2.5 flex items-center justify-between font-mono text-xs">
      {/* Left: View Title & System Status */}
      <div className="flex items-center gap-3">
        <div className="space-y-0.5">
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">
            {getViewBreadcrumb(activeView)}
          </p>
          <h1 className="text-sm font-bold text-slate-100 tracking-tight">RazorShield AI Risk Console</h1>
        </div>
        {renderConnectionBadge()}
      </div>

      {/* Center: System Environment Mode Banner */}
      <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px]">
        <span className="text-slate-400">ENVIRONMENT: <strong className="text-indigo-300">LOCAL</strong></span>
        <span className="text-slate-600">|</span>
        <span className="text-slate-400">DATA MODE: <strong className="text-emerald-400">LIVE</strong></span>
      </div>

      {/* Right: User Identity, Dev Simulation Role & System Controls */}
      <div className="flex items-center gap-3">
        {/* Pitch Teleprompter Mode Trigger (For Hackathon 5-Min Video Recording) */}
        {onOpenPitchTeleprompter && (
          <button
            onClick={onOpenPitchTeleprompter}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-600/30 to-indigo-600/30 hover:from-purple-600/40 hover:to-indigo-600/40 text-purple-300 border border-purple-500/50 font-bold transition-all shadow-sm shadow-purple-500/10 cursor-pointer animate-pulse-subtle"
            title="Start Interactive 5-Minute Pitch Recording Teleprompter"
          >
            <span className="text-xs">🎬</span>
            <span>Pitch Teleprompter</span>
          </button>
        )}

        {/* Guided Tour Trigger */}
        <button
          onClick={() => setShowGuidedTour(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 font-bold transition-all shadow-sm cursor-pointer"
          title="Open Step-by-Step Guided Tour"
        >
          <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
          <span>Guided Mode</span>
        </button>


        {/* User Identity & Dev Role Simulator */}
        <div className="flex items-center gap-2 bg-slate-950 px-3 py-1 rounded-lg border border-slate-800 shadow-inner">
          <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
          <div className="flex flex-col text-[10px]">
            <span className="font-bold text-slate-200">{user.name}</span>
            <div className="flex items-center gap-1">
              <span className="text-slate-400 text-[9px]">DEV SIMULATION:</span>
              <select
                value={devSimRole}
                onChange={(e) => setDevSimRole(e.target.value as UserRole)}
                aria-label="Dev Role Simulation"
                className="bg-slate-900 text-indigo-300 font-bold text-[10px] px-1 py-0.5 rounded border border-slate-700 focus:outline-none cursor-pointer hover:border-slate-600 transition-colors"
              >
                <option value="RISK_ANALYST" className="bg-slate-900 text-slate-100">RISK_ANALYST</option>
                <option value="OPERATOR" className="bg-slate-900 text-slate-100">OPERATOR</option>
                <option value="AUDITOR" className="bg-slate-900 text-slate-100">AUDITOR (Read-Only)</option>
                <option value="ADMIN" className="bg-slate-900 text-slate-100">ADMIN</option>
              </select>
            </div>
          </div>
        </div>

        {/* Command Palette Trigger */}
        {onOpenCommandPalette && (
          <button
            onClick={onOpenCommandPalette}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-400 border border-slate-800 transition-colors cursor-pointer"
          >
            <span>Search</span>
            <kbd className="px-1.5 py-0.5 text-[9px] bg-slate-800 text-indigo-400 rounded border border-slate-700">Ctrl K</kbd>
          </button>
        )}

        {/* System Time */}
        <div className="hidden sm:flex items-center gap-1.5 text-slate-400 bg-slate-950 px-2.5 py-1.5 rounded-lg border border-slate-800 text-[11px]">
          <Clock className="w-3.5 h-3.5 text-indigo-400" />
          <span>{timeStr}</span>
        </div>

        {/* Manual Sync Control */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors cursor-pointer"
            title="Refresh Real-Time System Data"
          >
            <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
            <span>Sync</span>
          </button>
        )}

        {/* Guided Tour Modal */}
        <GuidedModeTour isOpen={showGuidedTour} onClose={() => setShowGuidedTour(false)} />
      </div>
    </header>
  );
};

