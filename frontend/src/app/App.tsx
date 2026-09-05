import React, { useState, useEffect } from 'react';
import { Sidebar, NavView } from '../components/layout/Sidebar';
import { TopBar } from '../components/layout/TopBar';
import { NotificationToast } from '../components/layout/NotificationToast';
import { NotificationProvider } from '../providers/NotificationProvider';
import { KpiStrip } from '../components/command-center/KpiStrip';
import { SystemHealthGrid } from '../components/command-center/SystemHealthGrid';
import { LiveRiskStream } from '../components/command-center/LiveRiskStream';
import { RiskDistributionChart } from '../components/command-center/RiskDistributionChart';
import { ActiveThreatsList } from '../components/command-center/ActiveThreatsList';
import { TransactionTable } from '../components/live-transactions/TransactionTable';
import { InvestigationWorkspace } from '../components/investigations/InvestigationWorkspace';
import { ScenarioCardGrid } from '../components/simulator/ScenarioCardGrid';
import { ChaosLabPanel } from '../components/chaos/ChaosLabPanel';
import { BenchmarkDashboard } from '../components/evaluation/BenchmarkDashboard';
import { CommandPalette } from '../components/layout/CommandPalette';
import { ErrorBoundary } from '../components/layout/ErrorBoundary';
import { useSystemHealth } from '../hooks/useSystemHealth';
import { useIncidents } from '../hooks/useIncidents';
import { AuthProvider } from '../context/AuthContext';
import { realtimeStream } from '../services/sse';
import { getRecentTransactions } from '../services/investigations';
import { TransactionDecision } from '../types/domain';

import { AnalystWorkQueue } from '../components/work-queue/AnalystWorkQueue';
import { PitchTeleprompterOverlay } from '../components/layout/PitchTeleprompterOverlay';


function AppContent() {
  const [activeView, setActiveView] = useState<NavView>('command');
  const [commandPaletteOpen, setCommandPaletteOpen] = useState<boolean>(false);
  const [pitchTeleprompterOpen, setPitchTeleprompterOpen] = useState<boolean>(false);
  const [selectedInvestigationId, setSelectedInvestigationId] = useState<string>('cust_default');

  const { systemStatus, refetch: refetchHealth } = useSystemHealth();
  const { incidents, refetch: refetchIncidents } = useIncidents();

  const [recentDecisions, setRecentDecisions] = useState<TransactionDecision[]>([]);

  // Load initial recent transactions from backend API (0% fake seeding)
  const fetchRecent = async () => {
    try {
      const txns = await getRecentTransactions();
      setRecentDecisions(txns || []);
    } catch {
      setRecentDecisions([]);
    }
  };

  useEffect(() => {
    fetchRecent();

    // Subscribe to Real-Time SSE events for REST state rehydration
    const unsubscribe = realtimeStream.subscribeEvents((evt) => {
      if (evt.event_type === 'NEW_TRANSACTION' || evt.event_type === 'ACTION_EXECUTED') {
        fetchRecent();
      }
      if (evt.event_type === 'NEW_INCIDENT' || evt.event_type === 'INCIDENT_UPDATED') {
        refetchIncidents();
      }
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  const handleSelectInvestigation = (id: string) => {
    setSelectedInvestigationId(id);
    setActiveView('investigations');
  };

  const handleAddTransaction = (newTxn: TransactionDecision) => {
    setRecentDecisions((prev) => [newTxn, ...prev]);
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* GLOBAL ENTERPRISE SIDEBAR */}
      <Sidebar activeView={activeView} onSelectView={setActiveView} systemStatus={systemStatus} />

      {/* MAIN VIEW CONTAINER */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <TopBar
          activeView={activeView}
          systemStatus={systemStatus}
          onRefresh={() => {
            refetchHealth();
            fetchRecent();
          }}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          onOpenPitchTeleprompter={() => setPitchTeleprompterOpen(true)}
        />

        <main className="p-6 max-w-7xl w-full mx-auto space-y-6 flex-1">
          <ErrorBoundary key={activeView} fallbackTitle={`View Render Notice (${activeView.toUpperCase()})`}>
            {/* VIEW 0: ANALYST WORK QUEUE */}
            {activeView === 'work-queue' && (
              <div className="space-y-6 animate-in fade-in-50">
                <AnalystWorkQueue onSelectCase={handleSelectInvestigation} />
              </div>
            )}

            {/* VIEW 1: COMMAND CENTER */}
            {activeView === 'command' && (
              <div className="space-y-6 animate-in fade-in-50">
                <KpiStrip
                  systemStatus={systemStatus}
                  recentDecisions={recentDecisions}
                  activeIncidentsCount={incidents.length}
                  unsafeActionsCount={0}
                />
                <SystemHealthGrid systemStatus={systemStatus} />
                <div className="grid grid-cols-3 gap-6">
                  <div className="col-span-2">
                    <LiveRiskStream
                      decisions={recentDecisions}
                      onSelectTransaction={() => setActiveView('transactions')}
                    />
                  </div>
                  <div>
                    <RiskDistributionChart decisions={recentDecisions} />
                  </div>
                </div>
                <ActiveThreatsList onSelectInvestigation={handleSelectInvestigation} />
              </div>
            )}

            {/* VIEW 2: LIVE TRANSACTIONS */}
            {activeView === 'transactions' && (
              <div className="space-y-6 animate-in fade-in-50">
                <TransactionTable
                  decisions={recentDecisions}
                  onAddTransaction={handleAddTransaction}
                />
              </div>
            )}

            {/* VIEW 3-9: CORE INVESTIGATION WORKSPACE (Unified context) */}
            {(activeView === 'investigations' ||
              activeView === 'graph' ||
              activeView === 'ai' ||
              activeView === 'evidence' ||
              activeView === 'policies' ||
              activeView === 'actions' ||
              activeView === 'audit') && (
              <div className="space-y-6 animate-in fade-in-50">
                <InvestigationWorkspace investigationId={selectedInvestigationId} activeView={activeView} />
              </div>
            )}

            {/* VIEW 10: ATTACK SIMULATOR */}
            {activeView === 'simulator' && (
              <div className="space-y-6 animate-in fade-in-50">
                <ScenarioCardGrid />
              </div>
            )}

            {/* VIEW 11: CHAOS LAB */}
            {activeView === 'chaos' && (
              <div className="space-y-6 animate-in fade-in-50">
                <ChaosLabPanel />
              </div>
            )}

            {/* VIEW 12: EVALUATION BENCHMARKS */}
            {activeView === 'evaluation' && (
              <div className="space-y-6 animate-in fade-in-50">
                <BenchmarkDashboard />
              </div>
            )}
          </ErrorBoundary>
        </main>
      </div>

      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onSelectView={setActiveView}
      />
      <PitchTeleprompterOverlay
        isOpen={pitchTeleprompterOpen}
        onClose={() => setPitchTeleprompterOpen(false)}
        onSelectView={setActiveView}
      />
      <NotificationToast />

    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <AppContent />
      </NotificationProvider>
    </AuthProvider>
  );
}
