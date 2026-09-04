import React, { useState, useEffect } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  BackgroundVariant,
} from '@xyflow/react';

export interface PackageNodeInput {
  id: string;
  type?: string;
  label?: string;
  attributes?: Record<string, any>;
}

export interface PackageEdgeInput {
  id: string;
  source: string;
  target: string;
  relationship?: string;
  risk_weight?: number;
}

export interface GraphCanvasProps {
  packageNodes?: PackageNodeInput[];
  packageEdges?: PackageEdgeInput[];
}

const getNodeStyle = (type?: string) => {
  const t = (type || '').toUpperCase();
  if (t.includes('CUSTOMER') || t.includes('USER')) {
    return { background: '#1e1b4b', color: '#818cf8', border: '1px solid #6366f1', borderRadius: '8px', padding: '10px' };
  }
  if (t.includes('DEVICE') || t.includes('IP')) {
    return { background: '#31121d', color: '#f43f5e', border: '1px solid #f43f5e', borderRadius: '8px', padding: '10px' };
  }
  if (t.includes('MERCHANT')) {
    return { background: '#2e1065', color: '#c084fc', border: '1px solid #a855f7', borderRadius: '8px', padding: '10px' };
  }
  return { background: '#1e293b', color: '#cbd5e1', border: '1px solid #475569', borderRadius: '8px', padding: '10px' };
};

export default function GraphCanvas({ packageNodes, packageEdges }: GraphCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  useEffect(() => {
    if (packageNodes && packageNodes.length > 0) {
      const convertedNodes: Node[] = packageNodes.map((n, idx) => ({
        id: n.id,
        position: { x: 150 + (idx % 3) * 250, y: 50 + Math.floor(idx / 3) * 130 },
        data: { label: n.label || `${n.type || 'Node'}: ${n.id}` },
        style: getNodeStyle(n.type),
      }));
      setNodes(convertedNodes);
    } else {
      setNodes([]);
    }

    if (packageEdges && packageEdges.length > 0) {
      const convertedEdges: Edge[] = packageEdges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.relationship || 'LINKED',
        animated: (e.risk_weight || 0) >= 0.7,
        style: { stroke: (e.risk_weight || 0) >= 0.7 ? '#f43f5e' : '#6366f1' },
      }));
      setEdges(convertedEdges);
    } else {
      setEdges([]);
    }
  }, [packageNodes, packageEdges, setNodes, setEdges]);

  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  };

  return (
    <div className="space-y-4">
      <div className="h-[400px] w-full rounded-xl bg-slate-950 border border-slate-800 overflow-hidden relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
        >
          <Controls className="bg-slate-900 border-slate-800 text-slate-200" />
          <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
        </ReactFlow>
      </div>

      {selectedNode && (
        <div className="p-4 rounded-xl bg-slate-900 border border-indigo-500/40 text-xs font-mono space-y-1">
          <div className="text-indigo-400 font-bold">Selected Node Details (`InvestigationPackage.nodes`)</div>
          <div>Node ID: <span className="text-slate-200">{selectedNode.id}</span></div>
          <div>Label: <span className="text-slate-200">{String(selectedNode.data.label)}</span></div>
        </div>
      )}
    </div>
  );
}
