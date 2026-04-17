import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useEffect, useCallback } from 'react';
import { GitBranch } from 'lucide-react';

// ── 노드 아이콘/색상 매핑 ──────────────────────────────────
const AGENT_COLORS = {
  pm:         { bg: '#1e3a5f', border: '#3b82f6', label: 'CTO' },
  developer:  { bg: '#1a3a2a', border: '#22c55e', label: 'Developer' },
  designer:   { bg: '#3a1a3a', border: '#a855f7', label: 'Designer' },
  researcher: { bg: '#3a2a1a', border: '#f59e0b', label: 'Researcher' },
  analyst:    { bg: '#1a2a3a', border: '#06b6d4', label: 'Analyst' },
  reviewer:   { bg: '#3a2a1a', border: '#f97316', label: 'Reviewer' },
  default:    { bg: '#1e2030', border: '#4f6ef7', label: 'Agent' },
};

const STATUS_STYLES = {
  pending:   { glow: 'none', opacity: 0.5, badge: '⬜' },
  running:   { glow: '0 0 12px rgba(79, 142, 247, 0.7)', opacity: 1, badge: '🔵' },
  completed: { glow: '0 0 12px rgba(34, 197, 94, 0.6)', opacity: 1, badge: '✅' },
  error:     { glow: '0 0 12px rgba(239, 68, 68, 0.7)', opacity: 1, badge: '❌' },
};

// ── 커스텀 노드 컴포넌트 ──────────────────────────────────
function AgentNode({ data }) {
  const colors = AGENT_COLORS[data.role] || AGENT_COLORS.default;
  const statusStyle = STATUS_STYLES[data.status] || STATUS_STYLES.pending;
  const isActive = data.isActive;

  return (
    <div
      className={`agent-node ${isActive ? 'agent-node-active' : ''}`}
      style={{
        background: colors.bg,
        border: `1.5px solid ${colors.border}`,
        boxShadow: isActive
          ? `${statusStyle.glow}, 0 0 20px ${colors.border}66`
          : statusStyle.glow,
        opacity: statusStyle.opacity,
      }}
    >
      <div className="agent-node-badge">{statusStyle.badge}</div>
      <div className="agent-node-label">{data.label}</div>
      <div className="agent-node-role">{data.role}</div>
      {isActive && <div className="agent-node-pulse" style={{ borderColor: colors.border }} />}
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

// ── 레이아웃 계산 ──────────────────────────────────
function computeLayout(rawNodes, rawEdges, activeNode) {
  if (!rawNodes || rawNodes.length === 0) return { rfNodes: [], rfEdges: [] };

  const agentNodes = rawNodes.filter(n => n.id !== 'pm' && n.id !== 'reviewer');
  const xCenter = 300;
  const yStart = 80;
  const yStep = 120;

  const rfNodes = rawNodes.map(n => {
    let x, y;
    if (n.id === 'pm') {
      x = xCenter; y = yStart;
    } else if (n.id === 'reviewer') {
      x = xCenter + 200; y = yStart + yStep * (agentNodes.length + 1) / 2;
    } else {
      const idx = agentNodes.findIndex(a => a.id === n.id);
      x = xCenter - 180; y = yStart + yStep + idx * yStep;
    }
    return {
      id: n.id,
      type: 'agentNode',
      position: { x, y },
      data: {
        label: n.label,
        role: n.role,
        status: n.status,
        isActive: n.id === activeNode,
      },
    };
  });

  const rfEdges = (rawEdges || []).map((e, i) => ({
    id: `e-${i}`,
    source: e.from,
    target: e.to,
    animated: rawNodes.find(n => n.id === e.from)?.status === 'running',
    style: { stroke: '#2d3451', strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#2d3451' },
  }));

  return { rfNodes, rfEdges };
}

// ── 메인 NodeGraph 컴포넌트 ──────────────────────────────────
export default function NodeGraph({ nodeData }) {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const { rfNodes: newNodes, rfEdges: newEdges } = computeLayout(
      nodeData.nodes,
      nodeData.edges,
      nodeData.active_node
    );
    setRfNodes(newNodes);
    setRfEdges(newEdges);
  }, [nodeData, setRfNodes, setRfEdges]);

  const isEmpty = rfNodes.length === 0;

  return (
    <div className="node-graph-panel">
      {/* Header */}
      <div className="panel-header">
        <div className="panel-header-icon">
          <GitBranch size={14} />
        </div>
        <span>에이전트 워크플로우</span>
        {nodeData.active_node && (
          <span className="active-node-badge">▶ {nodeData.active_node}</span>
        )}
      </div>

      {/* Graph area */}
      <div className="graph-container">
        {isEmpty ? (
          <div className="graph-empty">
            <div className="graph-empty-icon">
              <GitBranch size={40} />
            </div>
            <p>워크플로우 대기 중</p>
            <p className="graph-empty-sub">CEO가 지시하면 에이전트 그래프가 표시됩니다</p>
            {/* Demo ghost nodes */}
            <div className="graph-ghost">
              <div className="ghost-node">CTO</div>
              <div className="ghost-arrow">↓</div>
              <div className="ghost-node">Developer</div>
              <div className="ghost-arrow">→</div>
              <div className="ghost-node">Reviewer</div>
            </div>
          </div>
        ) : (
          <ReactFlow
            nodes={rfNodes}
            edges={rfEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            minZoom={0.5}
            maxZoom={2}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#1e2030" gap={20} />
            <Controls style={{ background: '#111318', border: '1px solid #1e2030' }} />
            <MiniMap
              style={{ background: '#0a0b0e', border: '1px solid #1e2030' }}
              nodeColor={n => n.data?.status === 'completed' ? '#22c55e'
                : n.data?.status === 'running' ? '#3b82f6'
                : n.data?.status === 'error' ? '#ef4444'
                : '#2d3451'}
            />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}
