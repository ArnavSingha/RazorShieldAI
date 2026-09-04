import React from 'react';
import {
  ShieldAlert,
  Activity,
  CreditCard,
  Search,
  GitFork,
  BrainCircuit,
  FileCheck2,
  Sliders,
  Zap,
  History,
  FlaskConical,
  Flame,
  BarChart3,
  UserCheck
} from 'lucide-react';
import { SystemStatusData } from '../../types/domain';
import { useAuth } from '../../context/AuthContext';

export type NavView =
  | 'work-queue'
  | 'command'
  | 'transactions'
  | 'investigations'
  | 'graph'
  | 'ai'
  | 'evidence'
  | 'policies'
  | 'actions'
  | 'audit'
  | 'simulator'
  | 'chaos'
  | 'evaluation';

interface SidebarProps {
  activeView: NavView;
  onSelectView: (view: NavView) => void;
  systemStatus: SystemStatusData | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeView, onSelectView, systemStatus }) => {
  const { devSimRole } = useAuth();
  const sections = [
    {
      title: 'OPERATIONS',
      items: [
        { id: 'work-queue' as NavView, label: 'Analyst Work Queue', icon: ShieldAlert },
        { id: 'command' as NavView, label: 'Command Center', icon: Activity },
        { id: 'transactions' as NavView, label: 'Live Transactions', icon: CreditCard },
        { id: 'investigations' as NavView, label: 'Investigations', icon: Search },
      ],
    },
    {
      title: 'INTELLIGENCE',
      items: [
        { id: 'graph' as NavView, label: 'Fraud Graph', icon: GitFork },
        { id: 'ai' as NavView, label: 'AI Investigator', icon: BrainCircuit },
        { id: 'evidence' as NavView, label: 'Evidence Explorer', icon: FileCheck2 },
      ],
    },
    {
      title: 'CONTROL PLANE',
      items: [
        { id: 'policies' as NavView, label: 'Policy Decisions', icon: Sliders },
        { id: 'actions' as NavView, label: 'Action Gateway', icon: Zap },
        { id: 'audit' as NavView, label: 'Audit Trail', icon: History },
      ],
    },
    {
      title: 'RESILIENCE',
      items: [
        { id: 'simulator' as NavView, label: 'Attack Simulator', icon: FlaskConical },
        { id: 'chaos' as NavView, label: 'Chaos Lab', icon: Flame },
      ],
    },
    {
      title: 'EVALUATION',
      items: [
        { id: 'evaluation' as NavView, label: 'Benchmarks', icon: BarChart3 },
      ],
    },
  ];

  const getStatusColor = (status?: string) => {
    if (status === 'HEALTHY') return 'bg-emerald-500';
    if (status === 'DEGRADED') return 'bg-amber-500';
    if (status === 'OFFLINE') return 'bg-rose-500';
    return 'bg-slate-600';
  };

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800/80 flex flex-col justify-between shrink-0 select-none h-screen sticky top-0 overflow-hidden">
      {/* Brand Header */}
      <div className="flex flex-col flex-1 min-h-0">
        <div className="p-5 border-b border-slate-800/80 flex items-center gap-3 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shadow-sm shadow-indigo-500/10">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-slate-100">RazorShield AI</span>
            </div>
            <p className="text-[10px] font-mono text-slate-400 tracking-wider uppercase">Risk Operations Console</p>
          </div>
        </div>

        {/* Navigation Section Groups — Independently Scrollable Navigation Region */}
        <nav aria-label="Main Navigation" className="p-3 space-y-4 overflow-y-auto flex-1 min-h-0 custom-scrollbar">
          {sections.map((section) => (
            <div key={section.title} className="space-y-1">
              <p className="px-3 text-[10px] font-mono font-bold text-slate-400 tracking-wider uppercase">
                {section.title}
              </p>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeView === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => onSelectView(item.id)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950 ${
                        isActive
                          ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 font-semibold shadow-sm shadow-indigo-500/5'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-400' : 'text-slate-300'}`} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* Footer System Telemetry Status */}
      <div className="p-3.5 m-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
        <div className="flex justify-between items-center text-[11px] font-mono">
          <span className="text-slate-400">Environment</span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-indigo-400 font-bold uppercase border border-slate-700">
            {systemStatus?.environment || 'LOCAL'}
          </span>
        </div>

        {/* 7 Component Indicators Grid */}
        <div className="grid grid-cols-4 gap-1.5 pt-1 text-[10px] font-mono">
          <div className="flex items-center gap-1.5 text-slate-400" title="Gemini Reasoner">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus?.components?.gemini)}`} />
            <span>AI</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400" title="IsolationForest ML">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus?.components?.ml_engine)}`} />
            <span>ML</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400" title="Multi-Hop Graph">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus?.components?.graph_engine)}`} />
            <span>GRAPH</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400" title="Redis Fast Cache">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus?.components?.redis)}`} />
            <span>REDIS</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400" title="PostgreSQL Audit Data">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus?.components?.postgres)}`} />
            <span>PG</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400" title="Chained Audit Ledger">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus?.components?.audit)}`} />
            <span>AUDIT</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400" title="Action Gateway">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus?.components?.action_gateway)}`} />
            <span>GW</span>
          </div>
        </div>

        <div className="pt-1 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-1.5 min-w-0">
            <UserCheck className={`w-3.5 h-3.5 shrink-0 ${devSimRole === 'ADMIN' ? 'text-purple-400' : devSimRole === 'AUDITOR' ? 'text-amber-400' : devSimRole === 'OPERATOR' ? 'text-sky-400' : 'text-indigo-400'}`} />
            <span className={`font-bold truncate text-[10px] ${devSimRole === 'ADMIN' ? 'text-purple-300' : devSimRole === 'AUDITOR' ? 'text-amber-300' : devSimRole === 'OPERATOR' ? 'text-sky-300' : 'text-slate-300'}`}>
              {devSimRole}
            </span>
          </div>
          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border shrink-0 ${devSimRole === 'ADMIN' ? 'text-purple-400 bg-purple-500/10 border-purple-500/30' : devSimRole === 'AUDITOR' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'}`}>
            {devSimRole === 'ADMIN' ? 'SUPER' : 'AUTH'}
          </span>
        </div>
      </div>
    </aside>
  );
};
