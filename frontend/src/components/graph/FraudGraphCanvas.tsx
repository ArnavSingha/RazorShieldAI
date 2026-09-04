import React, { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { GraphNode, GraphEdge } from '../../types/domain';
import { User, CreditCard, Laptop, Globe, ShoppingBag, ShieldAlert } from 'lucide-react';

interface FraudGraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodeId?: string | null;
  highlightedEvidenceId?: string | null;
  onSelectNode?: (node: GraphNode | null) => void;
}

export const FraudGraphCanvas: React.FC<FraudGraphCanvasProps> = ({
  nodes: rawNodes,
  edges: rawEdges,
  selectedNodeId,
  highlightedEvidenceId,
  onSelectNode,
}) => {
  // Deterministic Graph Layout Calculation
  const initialNodes: Node[] = useMemo(() => {
    if (!rawNodes || rawNodes.length === 0) {
      // Fallback default demonstration nodes
      return [
        {
          id: 'cust_mule_101',
          type: 'default',
          position: { x: 100, y: 80 },
          data: { label: 'Customer: cust_mule_101 (Risk 95)' },
          style: { background: '#1e1b4b', color: '#f8fafc', border: '1px solid #6366f1', borderRadius: '8px', padding: '10px' },
        },
        {
          id: 'dev_fingerprint_99',
          type: 'default',
          position: { x: 350, y: 80 },
          data: { label: 'Device: dev_fingerprint_99 (Risk 88)' },
          style: { background: '#31121d', color: '#f8fafc', border: '1px solid #f43f5e', borderRadius: '8px', padding: '10px' },
        },
        {
          id: 'ip_proxy_192',
          type: 'default',
          position: { x: 600, y: 80 },
          data: { label: 'IP: 192.168.1.100 (Risk 90)' },
          style: { background: '#31121d', color: '#f8fafc', border: '1px solid #f43f5e', borderRadius: '8px', padding: '10px' },
        },
        {
          id: 'card_tok_77',
          type: 'default',
          position: { x: 225, y: 240 },
          data: { label: 'Card: tok_card_77 (Risk 82)' },
          style: { background: '#064e3b', color: '#f8fafc', border: '1px solid #10b981', borderRadius: '8px', padding: '10px' },
        },
        {
          id: 'merch_comp_001',
          type: 'default',
          position: { x: 475, y: 240 },
          data: { label: 'Merchant: merch_comp_001 (Risk 75)' },
          style: { background: '#3b0764', color: '#f8fafc', border: '1px solid #a855f7', borderRadius: '8px', padding: '10px' },
        },
      ];
    }

    // Deterministic position layout based on entity types
    const typeYMap: Record<string, number> = {
      CUSTOMER: 50,
      ACCOUNT: 160,
      DEVICE: 270,
      IP: 270,
      CARD_TOKEN: 380,
      MERCHANT: 380,
    };

    const typeCounts: Record<string, number> = {};

    return rawNodes.map((n) => {
      const type = n.entity_type || 'CUSTOMER';
      const count = typeCounts[type] || 0;
      typeCounts[type] = count + 1;

      const y = typeYMap[type] || 200;
      const x = 120 + count * 220;

      const isSelected = selectedNodeId === n.id;
      const isHighRisk = n.risk_score >= 60 || n.is_suspicious;

      let borderStyle = isSelected
        ? '2px solid #6366f1'
        : isHighRisk
        ? '1px solid #f43f5e'
        : '1px solid #334155';

      let bgStyle = isHighRisk ? '#1f1319' : '#0f172a';

      return {
        id: n.id,
        type: 'default',
        position: { x, y },
        data: {
          label: (
            <div className="flex items-center gap-2 font-mono text-xs p-1">
              <div className={`w-2 h-2 rounded-full ${isHighRisk ? 'bg-rose-500 animate-pulse' : 'bg-emerald-500'}`} />
              <div>
                <div className="font-bold text-slate-100">{n.label || n.id}</div>
                <div className="text-[10px] text-slate-400 font-sans">{type} • Risk {n.risk_score}</div>
              </div>
            </div>
          ),
        },
        style: {
          background: bgStyle,
          color: '#f8fafc',
          border: borderStyle,
          borderRadius: '8px',
          padding: '8px 12px',
          boxShadow: isSelected ? '0 0 15px rgba(99, 102, 241, 0.5)' : 'none',
        },
      };
    });
  }, [rawNodes, selectedNodeId]);

  const initialEdges: Edge[] = useMemo(() => {
    if (!rawEdges || rawEdges.length === 0) {
      return [
        { id: 'e1', source: 'cust_mule_101', target: 'dev_fingerprint_99', label: 'SHARED_DEVICE', animated: true, style: { stroke: '#f43f5e' } },
        { id: 'e2', source: 'dev_fingerprint_99', target: 'ip_proxy_192', label: 'SHARED_IP', animated: true, style: { stroke: '#f43f5e' } },
        { id: 'e3', source: 'cust_mule_101', target: 'card_tok_77', label: 'USED_CARD', style: { stroke: '#6366f1' } },
        { id: 'e4', source: 'card_tok_77', target: 'merch_comp_001', label: 'TRANSACTED_AT', style: { stroke: '#10b981' } },
      ];
    }

    return rawEdges.map((e) => {
      const isHighRisk = e.is_suspicious || e.weight >= 0.7;
      return {
        id: e.id || `e_${e.source}_${e.target}`,
        source: e.source,
        target: e.target,
        label: e.relation_type,
        animated: isHighRisk,
        style: {
          stroke: isHighRisk ? '#f43f5e' : '#6366f1',
          strokeWidth: isHighRisk ? 2 : 1,
        },
        labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'monospace' },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isHighRisk ? '#f43f5e' : '#6366f1',
        },
      };
    });
  }, [rawEdges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  React.useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  React.useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const found = rawNodes?.find((n) => n.id === node.id);
      if (found && onSelectNode) {
        onSelectNode(found);
      } else if (onSelectNode) {
        onSelectNode({
          id: node.id,
          entity_type: 'CUSTOMER',
          risk_score: 85,
          label: node.id,
          is_suspicious: true,
        });
      }
    },
    [rawNodes, onSelectNode]
  );

  return (
    <div className="w-full h-[520px] bg-slate-950 rounded-xl border border-slate-800 relative overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
      >
        <Background color="#1e293b" gap={16} size={1} />
        <Controls className="bg-slate-900 border-slate-800 fill-slate-300" />
        <MiniMap
          nodeColor={(node) => (node.id.includes('dev') || node.id.includes('proxy') ? '#f43f5e' : '#6366f1')}
          nodeStrokeColor="#0f172a"
          nodeBorderRadius={2}
          style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
          maskColor="rgba(2, 6, 23, 0.8)"
        />
      </ReactFlow>

      {/* Graph Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-10 bg-slate-900/90 border border-slate-800/90 p-3 rounded-lg backdrop-blur-md font-mono text-[10px] space-y-1.5 text-slate-300">
        <p className="font-bold text-slate-200 uppercase tracking-wider">Entity Graph Legend</p>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Critical / Mule Node</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Customer / Account</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Card Token</span>
        </div>
      </div>
    </div>
  );
};
