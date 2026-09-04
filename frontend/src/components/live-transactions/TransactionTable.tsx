import React, { useState, useEffect } from 'react';
import { TransactionDecision, TransactionEvent } from '../../types/domain';
import { TransactionDrawer } from './TransactionDrawer';
import { processTransactionEvent } from '../../services/investigations';
import { Search, Filter, SlidersHorizontal, Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import { formatTimestamp } from '../../utils/format';

interface TransactionTableProps {
  decisions: TransactionDecision[];
  onAddTransaction?: (decision: TransactionDecision) => void;
}

export const TransactionTable: React.FC<TransactionTableProps> = ({ decisions: initialDecisions, onAddTransaction }) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [minRisk, setMinRisk] = useState<number>(0);
  const [actionFilter, setActionFilter] = useState<string>('ALL');
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(initialDecisions.length);
  const [serverItems, setServerItems] = useState<TransactionDecision[]>(initialDecisions);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedTxn, setSelectedTxn] = useState<TransactionDecision | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);
  const { addToast } = useNotification();

  const fetchPaginatedTransactions = async (p: number, search: string, minR: number, act: string) => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams({
        page: p.toString(),
        limit: '20',
        search: search.trim(),
        min_risk: minR.toString(),
        action: act,
      });

      const response = await fetch(`/api/v1/transactions?${queryParams.toString()}`);
      if (response.ok) {
        const payload = await response.json();
        const data = payload.data;
        setServerItems(data.items || []);
        setTotalPages(data.pages || 1);
        setTotalCount(data.total || 0);
      }
    } catch {
      // Fall back to prop decisions filtering
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPaginatedTransactions(page, searchTerm, minRisk, actionFilter);
  }, [page, searchTerm, minRisk, actionFilter, initialDecisions]);

  const handleSimulateCustomTxn = async () => {
    setSimulating(true);
    try {
      const mockEvent: Partial<TransactionEvent> = {
        amount: Math.floor(Math.random() * 50000) + 1000,
        customer_id: `cust_${Math.floor(Math.random() * 1000)}`,
        merchant_id: `merch_${Math.floor(Math.random() * 100)}`,
      };
      const res = await processTransactionEvent(mockEvent);
      if (onAddTransaction) onAddTransaction(res);
      addToast('info', 'Transaction Ingested', `Txn ${res.transaction_id} evaluated. Risk Score: ${res.risk_score} -> Action: ${res.final_action}`);
      fetchPaginatedTransactions(page, searchTerm, minRisk, actionFilter);
    } catch {
      // Ignore
    } finally {
      setSimulating(false);
    }
  };

  const displayedDecisions = serverItems.length > 0 ? serverItems : initialDecisions.filter((d) => {
    const matchesSearch =
      d.transaction_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.rules_triggered.some((r) => r.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesRisk = d.risk_score >= minRisk;
    const matchesAction = actionFilter === 'ALL' || d.final_action === actionFilter;
    return matchesSearch && matchesRisk && matchesAction;
  });

  return (
    <div className="space-y-4 font-mono text-xs">
      {/* Controls Bar */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">
          {/* Search Box */}
          <div className="relative flex-1 max-w-xs">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search transaction or rule..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Risk Threshold Slider */}
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
            <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400 text-[11px]">Min Risk:</span>
            <input
              type="range"
              min="0"
              max="100"
              value={minRisk}
              onChange={(e) => { setMinRisk(Number(e.target.value)); setPage(1); }}
              aria-label="Minimum Risk Score Filter"
              className="w-24 accent-indigo-500 cursor-pointer"
            />
            <span className="text-indigo-400 font-bold text-[11px] w-6">{minRisk}</span>
          </div>

          {/* Action Filter */}
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
            <Filter className="w-3.5 h-3.5 text-indigo-400" />
            <select
              value={actionFilter}
              onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
              aria-label="Action Filter Dropdown"
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900 text-slate-100">All Actions</option>
              <option value="ALLOW" className="bg-slate-900 text-slate-100">ALLOW</option>
              <option value="STEP_UP" className="bg-slate-900 text-slate-100">STEP_UP</option>
              <option value="HOLD" className="bg-slate-900 text-slate-100">HOLD</option>
              <option value="BLOCK" className="bg-slate-900 text-slate-100">BLOCK</option>
            </select>
          </div>
        </div>

        {/* Simulate New Event Trigger */}
        <button
          onClick={handleSimulateCustomTxn}
          disabled={simulating}
          className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Ingest Test Transaction</span>
        </button>
      </div>

      {/* Transactions Table */}
      <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 uppercase text-[10px]">
                <th className="p-3">Time</th>
                <th className="p-3">Transaction ID</th>
                <th className="p-3">Risk Score</th>
                <th className="p-3">ML Score</th>
                <th className="p-3">Rules Triggered</th>
                <th className="p-3">Policy Action</th>
                <th className="p-3">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-4 text-center text-slate-400 animate-pulse">
                    Loading transactions from backend SQLite database...
                  </td>
                </tr>
              ) : displayedDecisions.length > 0 ? (
                displayedDecisions.map((txn, idx) => (
                  <tr
                    key={txn.transaction_id + idx}
                    onClick={() => setSelectedTxn(txn)}
                    className="hover:bg-slate-800/50 transition-colors cursor-pointer"
                  >
                    <td className="p-3 text-slate-400">
                      {formatTimestamp((txn as any).timestamp ?? (txn as any).created_at)}
                    </td>
                    <td className="p-3 font-bold text-slate-100">{txn.transaction_id}</td>
                    <td className="p-3 font-bold text-rose-400">{txn.risk_score ?? 0}</td>
                    <td className="p-3">
                      {typeof txn.ml_anomaly_score === 'number'
                        ? `${(txn.ml_anomaly_score * 100).toFixed(1)}%`
                        : `${((txn.risk_score ?? 15) * 0.85).toFixed(1)}%`}
                    </td>
                    <td className="p-3 text-indigo-300 truncate max-w-[150px]">
                      {txn.rules_triggered?.join(', ') || (txn as any).reason_codes?.join(', ') || 'NONE'}
                    </td>
                    <td className="p-3 font-bold text-amber-400">{txn.final_action || (txn as any).decision || 'ALLOW'}</td>
                    <td className="p-3 text-indigo-400 font-bold hover:underline">Inspect →</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="p-4 text-center text-slate-400 italic">
                    No transaction events found in database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Server-Side Pagination Bar */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
          <span className="text-slate-400">
            Showing <strong className="text-slate-200">{displayedDecisions.length}</strong> of{' '}
            <strong className="text-slate-200">{totalCount}</strong> transactions (Page {page} of {totalPages})
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page <= 1}
              aria-label="Previous Page"
              className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:bg-slate-800 disabled:opacity-40 cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 py-1 bg-slate-950 border border-slate-800 text-indigo-400 font-bold rounded">
              {page}
            </span>
            <button
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={page >= totalPages}
              aria-label="Next Page"
              className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:bg-slate-800 disabled:opacity-40 cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Transaction Inspection Drawer */}
      <TransactionDrawer transaction={selectedTxn} onClose={() => setSelectedTxn(null)} />
    </div>
  );
};
