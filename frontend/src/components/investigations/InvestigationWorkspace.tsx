import React, { useState, useEffect } from 'react';
import { IncidentHeader } from './IncidentHeader';
import { FraudGraphCanvas } from '../graph/FraudGraphCanvas';
import { NodeInspector } from '../graph/NodeInspector';
import { EvidenceExplorer } from './EvidenceExplorer';
import { AiInvestigatorPanel } from '../ai/AiInvestigatorPanel';
import { PolicyEnginePanel } from '../policy/PolicyEnginePanel';
import { ActionGatewayPanel } from '../actions/ActionGatewayPanel';
import { CryptographicAuditPanel } from '../audit/CryptographicAuditPanel';
import {
  InvestigationPackage,
  AgentInvestigationResult,
  PolicyDecision,
  ActionToken,
  ActionExecutionResult,
  AuditVerificationData,
  GraphNode,
} from '../../types/domain';
import {
  getGraphInvestigation,
  runAgentInvestigation,
  authorizeAction,
  executeActionToken,
} from '../../services/investigations';
import { verifyAuditLedger } from '../../services/audit';
import {
  fetchInvestigationTimeline,
  exportInvestigationCase,
  updateIncidentState,
  TimelineEventItem,
} from '../../services/timeline';
import { Play, Shield, Lock, Download, Clock, UserCheck, AlertTriangle, ShieldAlert, Zap } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import { useAuth } from '../../context/AuthContext';
import { formatTimestamp } from '../../utils/format';

interface InvestigationWorkspaceProps {
  investigationId: string;
  activeView?: string;
}

export const InvestigationWorkspace: React.FC<InvestigationWorkspaceProps> = ({ investigationId, activeView = 'investigations' }) => {
  const [activeTab, setActiveTab] = useState<string>(activeView);
  const [packageData, setPackageData] = useState<InvestigationPackage | null>(null);
  const [agentResult, setAgentResult] = useState<AgentInvestigationResult | null>(null);
  const [policyDecision, setPolicyDecision] = useState<PolicyDecision | null>(null);
  const [actionToken, setActionToken] = useState<ActionToken | null>(null);
  const [executionResult, setExecutionResult] = useState<ActionExecutionResult | null>(null);
  const [auditData, setAuditData] = useState<AuditVerificationData | null>(null);
  const [timeline, setTimeline] = useState<TimelineEventItem[]>([]);
  const [decisionPacket, setDecisionPacket] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    setActiveTab(activeView);
    // Smooth scroll to target section if a specific tool section was clicked
    if (activeView && activeView !== 'investigations') {
      const targetEl = document.getElementById(`workspace-section-${activeView}`);
      if (targetEl) {
        setTimeout(() => {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
      }
    }
  }, [activeView]);

  const [incidentStatus, setIncidentStatus] = useState<string>('INVESTIGATING');
  const [incidentOwner, setIncidentOwner] = useState<string>('Arnav Singha');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningAgent, setRunningAgent] = useState<boolean>(false);
  const [authorizing, setAuthorizing] = useState<boolean>(false);
  const [executing, setExecuting] = useState<boolean>(false);
  const [exporting, setExporting] = useState<boolean>(false);

  const { addToast } = useNotification();
  const { hasCapability, devSimRole } = useAuth();

  const canRunAi = hasCapability('ai.run');
  const canAuthorize = hasCapability('action.authorize');
  const canUpdate = hasCapability('investigation.update');
  const canExport = hasCapability('case.export');

  // Load investigation graph package, audit ledger, and timeline
  const loadInvestigation = async () => {
    setLoading(true);
    setAgentResult(null);
    setPolicyDecision(null);
    setActionToken(null);
    setExecutionResult(null);
    setDecisionPacket(null);

    try {
      const rawPkg: any = await getGraphInvestigation(investigationId);
      if (rawPkg) {
        const clusterRisk = rawPkg.cluster_risk || {};
        const finExposure = rawPkg.financial_exposure || {};
        const rawEvidence = rawPkg.evidence_items || rawPkg.primary_evidence || [];
        const rawNodes = rawPkg.nodes || [];
        const rawEdges = rawPkg.edges || [];

        const normalizedPkg: InvestigationPackage = {
          package_id: rawPkg.package_id || `PKG-${investigationId}`,
          incident_id: rawPkg.incident_id || `FR-${investigationId}`,
          entity_id: rawPkg.entity_id || investigationId,
          severity: rawPkg.severity || clusterRisk.severity || 'HIGH',
          risk_score: rawPkg.risk_score ?? clusterRisk.score ?? 75,
          confidence_score: rawPkg.confidence_score ?? (clusterRisk.confidence ? Math.round(clusterRisk.confidence * 100) : 94),
          affected_accounts_count: rawPkg.affected_accounts_count ?? (rawNodes.length || 4),
          total_financial_exposure_inr: rawPkg.total_financial_exposure_inr ?? finExposure.total_exposure_inr ?? 310000,
          evidence_snapshot_hash: rawPkg.evidence_snapshot_hash || 'a3b0c44298fc...',
          time_window: rawPkg.time_window || 'Last 24h',
          detected_patterns: (rawPkg.detected_patterns || []).map((p: any) => typeof p === 'string' ? p : p.pattern_type || 'ANOMALOUS_VELOCITY_CLUSTER'),
          created_at: rawPkg.created_at || Date.now() / 1000,
          evidence_items: rawEvidence.map((e: any, idx: number) => ({
            evidence_id: e.evidence_id || e.id || `E-${idx + 1}`,
            evidence_type: e.evidence_type || e.type || 'GRAPH_TRAVERSAL',
            claim: e.claim || 'Suspicious entity interaction detected in graph',
            confidence: e.confidence ? (e.confidence <= 1 ? Math.round(e.confidence * 100) : Math.round(e.confidence)) : 90,
            source_entities: e.source_entities || e.source_entity_ids || [],
            source_events: e.source_events || e.source_event_ids || [],
            observed_at: e.observed_at || Date.now() / 1000,
            freshness: e.freshness || 'Real-time',
          })),
          nodes: rawNodes.map((n: any) => ({
            id: n.node_id || n.id,
            entity_type: n.entity_type || 'CUSTOMER',
            risk_score: n.risk_score ?? (n.risk_weight ? Math.round(n.risk_weight * 100) : 75),
            label: n.entity_value || n.label || n.node_id || n.id,
            is_suspicious: n.risk_score >= 60 || n.is_suspicious || false,
            metadata: n.metadata || {},
          })),
          edges: rawEdges.map((e: any) => ({
            id: e.edge_id || e.id,
            source: e.source_id || e.source,
            target: e.target_id || e.target,
            relation_type: e.relationship_type || e.relation_type || 'TRANSACTED',
            weight: e.weight || 1.0,
            is_suspicious: e.weight >= 0.7 || e.is_suspicious || false,
            metadata: e.metadata || {},
          })),
        };
        setPackageData(normalizedPkg);
      } else {
        setPackageData(null);
      }
    } catch {
      setPackageData(null);
    }

    try {
      const tl = await fetchInvestigationTimeline(investigationId);
      setTimeline(tl);
    } catch {
      setTimeline([]);
    }

    try {
      const auditRes = await verifyAuditLedger();
      setAuditData(auditRes);
    } catch {
      setAuditData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvestigation();
  }, [investigationId]);

  // Step-by-Step Explicit Analyst Controls
  const handleRunAgent = async () => {
    if (!canRunAi) {
      addToast('error', 'Capability Denied', `Role '${devSimRole}' is View-Only. AI investigation execution is prohibited.`);
      return;
    }
    setRunningAgent(true);
    try {
      const res = await runAgentInvestigation(investigationId);
      setAgentResult(res);
      const tl = await fetchInvestigationTimeline(investigationId);
      setTimeline(tl);
      const confVal = res.confidence_score !== undefined
        ? (res.confidence_score <= 1.0 ? Math.round(res.confidence_score * 100) : Math.round(res.confidence_score))
        : (res.confidence !== undefined ? (res.confidence <= 1.0 ? Math.round(res.confidence * 100) : Math.round(res.confidence)) : 70);
      addToast('info', 'AI Reasoning Completed', `Gemini completed evaluation with ${confVal}% confidence. Recommendation: ${res.recommended_action}`);
    } catch (e: any) {
      addToast('error', 'AI Investigation Failed', e.message || 'Could not reach Gemini reasoning engine');
    } finally {
      setRunningAgent(false);
    }
  };

  const handleAuthorize = async () => {
    if (!canAuthorize) {
      addToast('error', 'Capability Denied', `Role '${devSimRole}' is View-Only. Action token authorization is prohibited.`);
      return;
    }
    setAuthorizing(true);
    try {
      const authRes = await authorizeAction(investigationId);
      if (authRes) {
        if (authRes.policy_decision) setPolicyDecision(authRes.policy_decision);
        if (authRes.action_token) setActionToken(authRes.action_token);
        if (authRes.decision_packet) setDecisionPacket(authRes.decision_packet);
        const tl = await fetchInvestigationTimeline(investigationId);
        setTimeline(tl);
        addToast('success', 'Action Authorized', `Deterministic Policy Engine authorized token: ${authRes.action_token?.token_id}`);
      }
    } catch (e: any) {
      addToast('error', 'Authorization Denied', e.message || 'Policy evaluation rejected action token issuance');
    } finally {
      setAuthorizing(false);
    }
  };

  const handleExecute = async () => {
    if (!actionToken) return;
    setExecuting(true);
    try {
      const res = await executeActionToken(actionToken);
      setExecutionResult(res);
      const auditRes = await verifyAuditLedger();
      setAuditData(auditRes);
      const tl = await fetchInvestigationTimeline(investigationId);
      setTimeline(tl);
      addToast('success', 'Action Executed & Verified', `Outcome: ${res.observed_outcome} (${res.execution_status}). Audit reference: ${res.audit_event_id}`);
    } catch (e: any) {
      addToast('error', 'Execution Failed', e.message || 'Action Gateway rejected execution');
    } finally {
      setExecuting(false);
    }
  };

  const handleUpdateStatus = async (newStatus: string) => {
    if (!canUpdate) {
      addToast('error', 'Capability Denied', `Role '${devSimRole}' is View-Only. Incident state updates are prohibited.`);
      return;
    }
    try {
      await updateIncidentState(investigationId, { status: newStatus, owner: incidentOwner });
      setIncidentStatus(newStatus);
      const tl = await fetchInvestigationTimeline(investigationId);
      setTimeline(tl);
      const auditRes = await verifyAuditLedger();
      setAuditData(auditRes);
      addToast('success', 'Incident State Updated', `Incident status set to '${newStatus}'. Audit block generated.`);
    } catch (e: any) {
      addToast('error', 'Update Failed', e.message || 'Could not update incident state');
    }
  };

  const handleExportCase = async () => {
    if (!canExport) {
      addToast('error', 'Capability Denied', `Role '${devSimRole}' is View-Only. Case report exports are prohibited.`);
      return;
    }
    setExporting(true);
    try {
      const reportData = await exportInvestigationCase(investigationId);
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `RazorShield_Case_Report_${investigationId}_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      addToast('success', 'Case Report Exported', `Investigation report downloaded cleanly.`);
    } catch (e: any) {
      addToast('error', 'Export Failed', e.message || 'Could not export case report');
    } finally {
      setExporting(false);
    }
  };

  // Why Flagged Reasons Derived from Package Data
  const whyFlaggedReasons = (packageData?.detected_patterns || []).map((p: any) => {
    if (typeof p === 'string') {
      return {
        code: p,
        impact: packageData?.risk_score || 75,
        desc: `Detected graph pattern ${p}`,
        evidence_ids: packageData?.evidence_items?.map((e) => e.evidence_id) || [],
      };
    }
    return {
      code: p.pattern_type || 'ANOMALOUS_VELOCITY_CLUSTER',
      impact: Math.round((p.weight || 0.75) * 100),
      desc: p.description || 'Elevated risk pattern',
      evidence_ids: p.evidence_ids || [],
    };
  });
  if (whyFlaggedReasons.length === 0) {
    whyFlaggedReasons.push({
      code: 'ANOMALOUS_VELOCITY_CLUSTER',
      impact: packageData?.risk_score || 75,
      desc: 'Multi-hop graph entity clustering & elevated risk score',
      evidence_ids: packageData?.evidence_items?.map((e) => e.evidence_id) || [],
    });
  }

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* INCIDENT HEADER */}
      <IncidentHeader packageData={packageData} />

      {/* READ-ONLY AUDITOR BANNER */}
      {devSimRole === 'AUDITOR' && (
        <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-300 flex items-center justify-between font-sans">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0" />
            <span>
              <strong>AUDITOR VIEW-ONLY MODE ACTIVE:</strong> Operational mutation controls, AI execution, ActionToken authorization, and Case Export are strictly disabled by capability policy.
            </span>
          </div>
          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-200 border border-amber-500/40 font-mono text-[10px]">
            READ-ONLY
          </span>
        </div>
      )}

      {/* ANALYST OPERATING COMMAND BAR */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between gap-4 flex-wrap">
        {/* Target & Incident Management */}
        <div className="flex items-center gap-3">
          <Shield className="w-4 h-4 text-indigo-400" />
          <span className="text-slate-200 font-bold">Analyst Control:</span>
          <code className="text-indigo-300 px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30">{investigationId}</code>

          {/* Status Dropdown */}
          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
            <span className="text-slate-400 text-[10px]">Status:</span>
            <select
              value={incidentStatus}
              disabled={!canUpdate}
              onChange={(e) => handleUpdateStatus(e.target.value)}
              aria-label="Incident Status Dropdown"
              className="bg-transparent text-slate-200 font-bold focus:outline-none cursor-pointer disabled:opacity-50"
            >
              <option value="NEW" className="bg-slate-900 text-slate-100">NEW</option>
              <option value="INVESTIGATING" className="bg-slate-900 text-slate-100">INVESTIGATING</option>
              <option value="REVIEW" className="bg-slate-900 text-slate-100">REVIEW</option>
              <option value="RESOLVED" className="bg-slate-900 text-slate-100">RESOLVED</option>
              <option value="FALSE_POSITIVE" className="bg-slate-900 text-slate-100">FALSE_POSITIVE</option>
            </select>
          </div>

          {/* Owner Input */}
          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
            <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
            <input
              type="text"
              value={incidentOwner}
              disabled={!canUpdate}
              onChange={(e) => setIncidentOwner(e.target.value)}
              onBlur={() => handleUpdateStatus(incidentStatus)}
              aria-label="Assign Analyst Input"
              className="bg-transparent text-slate-200 w-36 focus:outline-none disabled:opacity-50"
              placeholder="Assign Analyst..."
            />
          </div>
        </div>

        {/* Action Trigger Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCase}
            disabled={exporting || !canExport}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
            title={!canExport ? 'Auditor role is prohibited from exporting cases' : 'Export case report JSON'}
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>{exporting ? 'Exporting...' : 'Export Case Report'}</span>
          </button>

          <button
            onClick={handleRunAgent}
            disabled={runningAgent || !canRunAi}
            className="px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 disabled:opacity-40 text-purple-300 border border-purple-500/40 font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
            title={!canRunAi ? 'Auditor role is prohibited from triggering AI' : 'Run Gemini AI investigation'}
          >
            <Play className="w-3.5 h-3.5 text-purple-400 fill-purple-400" />
            <span>{runningAgent ? 'Running Gemini...' : '1. Run AI'}</span>
          </button>

          <button
            onClick={handleAuthorize}
            disabled={authorizing || !canAuthorize}
            className="px-3 py-1.5 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 disabled:opacity-40 text-amber-300 border border-amber-500/40 font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
            title={!canAuthorize ? 'Auditor role is prohibited from authorizing tokens' : 'Authorize Action Token'}
          >
            <Lock className="w-3.5 h-3.5 text-amber-400" />
            <span>2. Authorize Action</span>
          </button>

          <button
            onClick={handleExecute}
            disabled={executing || !actionToken}
            className="px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 disabled:opacity-40 text-emerald-300 border border-emerald-500/40 font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
            title={!actionToken ? 'Authorization required before execution' : 'Execute Action Token'}
          >
            <Zap className="w-3.5 h-3.5 text-emerald-400" />
            <span>3. Execute Action</span>
          </button>
        </div>
      </div>

      {/* WHY FLAGGED / RISK ATTRIBUTION CARDS */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 font-mono text-xs">
        <div className="flex justify-between items-center text-slate-300 font-bold text-xs uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            Why Flagged? Risk Attribution Breakdown
          </span>
          <span className="text-slate-400">Deterministic Provenance</span>
        </div>
        <div className="grid grid-cols-3 gap-3 pt-1">
          {whyFlaggedReasons.map((reason, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-slate-200">{reason.code}</span>
                <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold text-[10px]">
                  +{reason.impact} Risk
                </span>
              </div>
              <p className="text-[11px] text-slate-400">{reason.desc}</p>
              {reason.evidence_ids.length > 0 && (
                <div className="flex items-center gap-1 pt-1 overflow-x-auto custom-scrollbar">
                  <span className="text-[9px] text-slate-400 uppercase">Deep Link:</span>
                  {reason.evidence_ids.map((evId: string) => (
                    <button
                      key={evId}
                      onClick={() => setSelectedEvidenceId(evId)}
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold border transition-colors cursor-pointer ${
                        selectedEvidenceId === evId
                          ? 'bg-indigo-600 text-white border-indigo-400'
                          : 'bg-slate-900 text-indigo-300 border-indigo-500/30 hover:bg-indigo-900/40'
                      }`}
                    >
                      {evId}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* FLAGSHIP INVESTIGATION GRID LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Fraud Graph, Node Inspector, Policies, Actions, Audit */}
        <div className="lg:col-span-2 space-y-6">
          {/* FRAUD GRAPH CANVAS SECTION */}
          <div
            id="workspace-section-graph"
            className={`transition-all rounded-xl ${
              activeTab === 'graph' ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-slate-950 p-1 bg-indigo-950/20' : ''
            }`}
          >
            {activeTab === 'graph' && (
              <div className="mb-2 px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 font-bold text-xs flex items-center justify-between">
                <span>FOCUS: Fraud Graph Visualizer</span>
                <span className="text-[10px] text-indigo-400">Multi-Hop Entity Link Analysis</span>
              </div>
            )}
            <div className="flex gap-4">
              <div className="flex-1">
                <FraudGraphCanvas
                  nodes={packageData?.nodes || []}
                  edges={packageData?.edges || []}
                  selectedNodeId={selectedNode?.id}
                  highlightedEvidenceId={selectedEvidenceId}
                  onSelectNode={(n) => setSelectedNode(n)}
                />
              </div>
              {selectedNode && (
                <NodeInspector node={selectedNode} onClose={() => setSelectedNode(null)} />
              )}
            </div>
          </div>

          {/* POLICY ENGINE & OVERRIDE PANEL */}
          <div
            id="workspace-section-policies"
            className={`transition-all rounded-xl ${
              activeTab === 'policies' ? 'ring-2 ring-amber-500 ring-offset-2 ring-offset-slate-950 p-1 bg-amber-950/20' : ''
            }`}
          >
            {activeTab === 'policies' && (
              <div className="mb-2 px-3 py-1.5 rounded-lg bg-amber-600/20 border border-amber-500/40 text-amber-300 font-bold text-xs flex items-center justify-between">
                <span>FOCUS: Deterministic Policy Engine & Rules</span>
                <span className="text-[10px] text-amber-400">SLA & RBAC Policy Evaluation</span>
              </div>
            )}
            <PolicyEnginePanel policyDecision={policyDecision} agentResult={agentResult} />
          </div>

          {/* ACTION GATEWAY STATE MACHINE */}
          <div
            id="workspace-section-actions"
            className={`transition-all rounded-xl ${
              activeTab === 'actions' ? 'ring-2 ring-emerald-500 ring-offset-2 ring-offset-slate-950 p-1 bg-emerald-950/20' : ''
            }`}
          >
            {activeTab === 'actions' && (
              <div className="mb-2 px-3 py-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 font-bold text-xs flex items-center justify-between">
                <span>FOCUS: Action Gateway & Token Authorization</span>
                <span className="text-[10px] text-emerald-400">Fail-Closed Single-Use Action Token Gate</span>
              </div>
            )}
            <ActionGatewayPanel
              actionToken={actionToken}
              executionResult={executionResult}
              onExecuteToken={handleExecute}
              isExecuting={executing}
              decisionPacket={decisionPacket}
            />
          </div>

          {/* CRYPTOGRAPHIC AUDIT LEDGER */}
          <div
            id="workspace-section-audit"
            className={`transition-all rounded-xl ${
              activeTab === 'audit' ? 'ring-2 ring-cyan-500 ring-offset-2 ring-offset-slate-950 p-1 bg-cyan-950/20' : ''
            }`}
          >
            {activeTab === 'audit' && (
              <div className="mb-2 px-3 py-1.5 rounded-lg bg-cyan-600/20 border border-cyan-500/40 text-cyan-300 font-bold text-xs flex items-center justify-between">
                <span>FOCUS: Cryptographic SHA-256 Audit Trail</span>
                <span className="text-[10px] text-cyan-400">Verifiable Audit Ledger Chain</span>
              </div>
            )}
            <CryptographicAuditPanel auditData={auditData} />
          </div>
        </div>

        {/* Right 1 Column: Evidence Explorer, AI Panel & Investigation Timeline */}
        <div className="space-y-6">
          {/* EVIDENCE EXPLORER */}
          <div
            id="workspace-section-evidence"
            className={`transition-all rounded-xl ${
              activeTab === 'evidence' ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-slate-950 p-1 bg-indigo-950/20' : ''
            }`}
          >
            {activeTab === 'evidence' && (
              <div className="mb-2 px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 font-bold text-xs flex items-center justify-between">
                <span>FOCUS: Grounded Evidence Explorer</span>
                <span className="text-[10px] text-indigo-400">Cryptographically Grounded Items</span>
              </div>
            )}
            <EvidenceExplorer
              evidenceItems={packageData?.evidence_items || []}
              selectedEvidenceId={selectedEvidenceId}
              onSelectEvidence={(evId) => setSelectedEvidenceId(evId)}
            />
          </div>

          {/* GEMINI INVESTIGATOR REASONING PANEL */}
          <div
            id="workspace-section-ai"
            className={`transition-all rounded-xl ${
              activeTab === 'ai' ? 'ring-2 ring-purple-500 ring-offset-2 ring-offset-slate-950 p-1 bg-purple-950/20' : ''
            }`}
          >
            {activeTab === 'ai' && (
              <div className="mb-2 px-3 py-1.5 rounded-lg bg-purple-600/20 border border-purple-500/40 text-purple-300 font-bold text-xs flex items-center justify-between">
                <span>FOCUS: Gemini Autonomous AI Reasoning</span>
                <span className="text-[10px] text-purple-400">Structured AI Reasoning & Claims</span>
              </div>
            )}
            <AiInvestigatorPanel agentResult={agentResult} onRunAgent={handleRunAgent} />
          </div>

          {/* PERSISTENT INVESTIGATION TIMELINE */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 font-mono">
            <div className="flex justify-between items-center border-b border-slate-800 pb-2">
              <span className="flex items-center gap-1.5 text-slate-200 font-bold text-xs uppercase">
                <Clock className="w-4 h-4 text-indigo-400" />
                Investigation Timeline
              </span>
              <span className="text-[10px] text-slate-500">{timeline.length} Events</span>
            </div>

            {timeline.length > 0 ? (
              <div className="space-y-3 relative before:absolute before:inset-0 before:left-2 before:w-0.5 before:bg-slate-800">
                {timeline.map((evt, idx) => (
                  <div key={evt.event_id || idx} className="flex gap-3 items-start relative pl-6">
                    <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 absolute left-1 top-1 ring-4 ring-slate-900" />
                    <div className="space-y-0.5 flex-1">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="font-bold text-indigo-400 uppercase">{evt.stage}</span>
                        <span className="text-slate-500">
                          {formatTimestamp(evt.timestamp)}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-200">{evt.summary}</p>
                      <span className="text-[9px] text-slate-500 block">Actor: {evt.actor}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-slate-500 italic">
                Awaiting investigation timeline events.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
