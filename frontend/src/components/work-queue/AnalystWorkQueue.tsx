import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Clock,
  UserCheck,
  Filter,
  RefreshCw,
  Search,
  ChevronRight,
  AlertTriangle,
  Lock,
  ArrowUpDown,
  CheckCircle2,
} from 'lucide-react';
import { fetchApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useNotification } from '../../providers/NotificationProvider';

export type WorkQueueFilter =
  | 'ALL'
  | 'MY_CASES'
  | 'UNASSIGNED'
  | 'CRITICAL'
  | 'HIGH_EXPOSURE'
  | 'SLA_AT_RISK';

export interface WorkQueueItem {
  incident_id: string;
  investigation_id: string;
  name: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  priority: string;
  risk_score: number;
  confidence: number;
  protected_exposure_inr: number;
  status: string;
  owner: string;
  affected_entities: string[];
  detected_patterns: string[];
  created_at: number;
  updated_at: number;
  sla_target_seconds: number;
  sla_deadline: number;
  sla_seconds_remaining: number;
  sla_status: 'HEALTHY' | 'AT_RISK' | 'BREACHED';
  age_seconds: number;
  required_action: string;
}

interface AnalystWorkQueueProps {
  onSelectCase: (investigationId: string) => void;
}

export const AnalystWorkQueue: React.FC<AnalystWorkQueueProps> = ({ onSelectCase }) => {
  const [items, setItems] = useState<WorkQueueItem[]>([]);
  const [filter, setFilter] = useState<WorkQueueFilter>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  const { user, hasCapability, devSimRole } = useAuth();
  const { addToast } = useNotification();

  const fetchWorkQueue = async () => {
    setLoading(true);
    try {
      const res = await fetchApi<{ total_count: number; queue_items: WorkQueueItem[] }>(
        `/api/v1/work-queue?filter_type=${filter}`
      );
      setItems(res.queue_items || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkQueue();
    const timer = setInterval(fetchWorkQueue, 10000);
    return () => clearInterval(timer);
  }, [filter]);

  const filteredItems = items.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.incident_id.toLowerCase().includes(q) ||
      item.investigation_id.toLowerCase().includes(q) ||
      item.owner.toLowerCase().includes(q) ||
      item.detected_patterns.some((p) => p.toLowerCase().includes(q))
    );
  });

  const formatTimeRemaining = (secs: number) => {
    if (secs <= 0) return '00:00:00 (BREACHED)';
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4 font-mono text-xs">
      {/* QUEUE HEADER & METRICS */}
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between flex-wrap gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-indigo-400" />
            <h1 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Analyst Work Queue & Incident Intake
            </h1>
          </div>
          <p className="text-[11px] text-slate-400 font-sans mt-0.5">
            Real-time SLA-monitored fraud cases requiring investigation, analyst review, or action authorization.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchWorkQueue}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-indigo-400 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Cases</span>
          </button>
        </div>
      </div>

      {/* FILTER TABS & SEARCH BAR */}
      <div className="flex items-center justify-between gap-4 flex-wrap bg-slate-950 p-2.5 rounded-xl border border-slate-800">
        <div className="flex items-center gap-1 overflow-x-auto custom-scrollbar">
          {(
            [
              { id: 'ALL', label: 'All Active Cases' },
              { id: 'MY_CASES', label: 'My Cases' },
              { id: 'UNASSIGNED', label: 'Unassigned Queue' },
              { id: 'CRITICAL', label: 'Critical Risk' },
              { id: 'HIGH_EXPOSURE', label: 'High Exposure (≥ ₹100k)' },
              { id: 'SLA_AT_RISK', label: 'SLA At Risk / Breached' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id as WorkQueueFilter)}
              className={`px-3 py-1.5 rounded-lg font-bold transition-colors text-[11px] cursor-pointer whitespace-nowrap ${
                filter === tab.id
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search cases, customers, rules..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-slate-900 text-slate-200 pl-8 pr-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-indigo-500 text-[11px] w-64"
          />
        </div>
      </div>

      {/* WORK QUEUE DATA TABLE */}
      <div className="rounded-xl bg-slate-900/90 border border-slate-800 overflow-hidden shadow-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-950/80 border-b border-slate-800 text-[10px] text-slate-400 uppercase tracking-wider font-bold">
              <th className="py-3 px-4">Priority / Case</th>
              <th className="py-3 px-4">Target Entity</th>
              <th className="py-3 px-4">Risk Score</th>
              <th className="py-3 px-4">Exposure (INR)</th>
              <th className="py-3 px-4">SLA Countdown</th>
              <th className="py-3 px-4">Owner</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-[11px]">
            {filteredItems.length > 0 ? (
              filteredItems.map((item) => (
                <tr
                  key={item.incident_id}
                  onClick={() => onSelectCase(item.investigation_id)}
                  className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                >
                  <td className="py-3.5 px-4 font-bold">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          item.severity === 'CRITICAL'
                            ? 'bg-rose-500 animate-ping'
                            : item.severity === 'HIGH'
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                      />
                      <span className="text-slate-100 group-hover:text-indigo-300 font-mono">
                        {item.incident_id}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-indigo-400 font-bold">
                    {item.investigation_id}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded font-extrabold text-[10px] ${
                        item.risk_score >= 80
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : item.risk_score >= 60
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      }`}
                    >
                      {item.risk_score} / 100
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-200 font-bold">
                    ₹{item.protected_exposure_inr.toLocaleString()}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold flex items-center gap-1.5 w-max ${
                        item.sla_status === 'BREACHED'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse'
                          : item.sla_status === 'AT_RISK'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          : 'bg-slate-800 text-slate-300 border border-slate-700'
                      }`}
                    >
                      <Clock className="w-3 h-3 text-indigo-400" />
                      <span>{formatTimeRemaining(item.sla_seconds_remaining)}</span>
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">
                    <span className="flex items-center gap-1">
                      <UserCheck className="w-3.5 h-3.5 text-slate-500" />
                      {item.owner}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800 font-bold text-[10px]">
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCase(item.investigation_id);
                      }}
                      className="px-3 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white font-bold transition-colors inline-flex items-center gap-1"
                    >
                      <span>Investigate</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8} className="py-12 text-center text-slate-400 italic font-sans">
                  No active work queue cases matching current filter ({filter}).
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
