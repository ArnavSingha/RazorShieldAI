import React, { useState, useEffect } from 'react';
import { NavView } from './Sidebar';
import { Search, Activity, CreditCard, GitFork, BrainCircuit, FileCheck2, Sliders, Zap, History, FlaskConical, Flame, BarChart3, X, Database, ShieldAlert } from 'lucide-react';
import { executeGlobalSearch, SearchResultItem } from '../../services/search';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectView: (view: NavView) => void;
  onSelectInvestigation?: (invId: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectView,
  onSelectInvestigation,
}) => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [searching, setSearching] = useState<boolean>(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Execute global search API when query changes
  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await executeGlobalSearch(query);
        setSearchResults(res.results || []);
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  const commands = [
    { id: 'work-queue' as NavView, label: 'Analyst Work Queue', group: 'OPERATIONS', icon: ShieldAlert },
    { id: 'command' as NavView, label: 'Command Center Dashboard', group: 'OPERATIONS', icon: Activity },
    { id: 'transactions' as NavView, label: 'Live Transactions Stream', group: 'OPERATIONS', icon: CreditCard },
    { id: 'investigations' as NavView, label: 'Active Investigation Workspace', group: 'OPERATIONS', icon: Search },
    { id: 'graph' as NavView, label: 'Multi-Hop Entity Fraud Graph', group: 'INTELLIGENCE', icon: GitFork },
    { id: 'ai' as NavView, label: 'Gemini Autonomous Investigator', group: 'INTELLIGENCE', icon: BrainCircuit },
    { id: 'evidence' as NavView, label: 'Grounded Evidence Explorer', group: 'INTELLIGENCE', icon: FileCheck2 },
    { id: 'policies' as NavView, label: 'Deterministic Policy Decisions', group: 'CONTROL PLANE', icon: Sliders },
    { id: 'actions' as NavView, label: 'Action Gateway & Token Issuance', group: 'CONTROL PLANE', icon: Zap },
    { id: 'audit' as NavView, label: 'Cryptographic SHA-256 Audit Trail', group: 'CONTROL PLANE', icon: History },
    { id: 'simulator' as NavView, label: 'Adversarial Threat Simulator', group: 'RESILIENCE', icon: FlaskConical },
    { id: 'chaos' as NavView, label: 'Chaos Engineering & Fault Lab', group: 'RESILIENCE', icon: Flame },
    { id: 'evaluation' as NavView, label: '3-Track Empirical Benchmarks', group: 'EVALUATION', icon: BarChart3 },
  ];

  const filteredCommands = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase()) || c.group.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-start justify-center pt-24 p-4 animate-in fade-in-50">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-w-xl w-full overflow-hidden font-mono text-xs">
        <div className="p-3 border-b border-slate-800 flex items-center gap-3">
          <Search className="w-4 h-4 text-indigo-400 shrink-0" />
          <input
            type="text"
            placeholder="Search database (e.g. txn_1001, cust_1, INC-8801, Graph)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-slate-100 placeholder-slate-500 focus:outline-none text-xs"
            autoFocus
          />
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto p-2 space-y-3 custom-scrollbar">
          {/* BACKEND SEARCH RESULTS */}
          {searchResults.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] text-indigo-400 font-bold px-3 uppercase tracking-wider block">
                Database Search Results ({searchResults.length})
              </span>
              {searchResults.map((item, idx) => (
                <button
                  key={item.id + idx}
                  onClick={() => {
                    if (onSelectInvestigation) onSelectInvestigation(item.link_id || item.id);
                    onSelectView('investigations');
                    onClose();
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800 text-slate-200 transition-colors text-left cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <Database className="w-4 h-4 text-amber-400" />
                    <div>
                      <span className="font-bold text-slate-100 block">{item.title}</span>
                      <span className="text-[10px] text-slate-400 block">{item.subtitle}</span>
                    </div>
                  </div>
                  <span className="text-[9px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase font-bold">
                    {item.category}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* VIEW NAVIGATION COMMANDS */}
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 font-bold px-3 uppercase tracking-wider block">
              Console Navigation
            </span>
            {filteredCommands.length > 0 ? (
              filteredCommands.map((cmd) => {
                const Icon = cmd.icon;
                return (
                  <button
                    key={cmd.id}
                    onClick={() => {
                      onSelectView(cmd.id);
                      onClose();
                    }}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-indigo-600/20 hover:text-indigo-300 text-slate-300 transition-colors text-left group cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-4 h-4 text-indigo-400 group-hover:text-indigo-300" />
                      <span>{cmd.label}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-sans uppercase">{cmd.group}</span>
                  </button>
                );
              })
            ) : (
              !searchResults.length && (
                <div className="p-4 text-center text-slate-500 italic">No matching results found in database or views</div>
              )
            )}
          </div>
        </div>

        <div className="p-2.5 bg-slate-950 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
          <span>Press <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-400">Esc</kbd> to close</span>
          <span>Backend Global Search Connected</span>
        </div>
      </div>
    </div>
  );
};
