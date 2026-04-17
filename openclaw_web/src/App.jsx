import { useMemo } from 'react';
import ChatPanel from './components/ChatPanel';
import NodeGraph from './components/NodeGraph';
import AgentLogPanel from './components/AgentLogPanel';
import AgentRosterPanel from './components/AgentRosterPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { Cpu, Wifi, WifiOff, Activity } from 'lucide-react';
import './index.css';

// Generate a stable client ID per browser session
const CLIENT_ID = `ceo_${Math.random().toString(36).substring(2, 10)}`;

export default function App() {
  const {
    isConnected,
    messages,
    agentLogs,
    nodeData,
    statusText,
    sendTask,
  } = useWebSocket(CLIENT_ID);

  const activeAgentCount = useMemo(() => {
    return nodeData.nodes?.filter(n => n.status === 'running').length || 0;
  }, [nodeData]);

  return (
    <div className="app-root">
      {/* ── Title Bar ─────────────────────────────── */}
      <div className="title-bar">
        <div className="title-bar-left">
          <div className="app-logo">
            <Cpu size={16} />
          </div>
          <span className="app-title">GeminiClaw</span>
          <span className="app-subtitle">AI Agent Orchestration Platform</span>
        </div>
        <div className="title-bar-right">
          {isConnected ? (
            <>
              <Wifi size={14} className="icon-connected" />
              <span className="status-connected">Connected</span>
            </>
          ) : (
            <>
              <WifiOff size={14} className="icon-disconnected" />
              <span className="status-disconnected">Disconnected</span>
            </>
          )}
          {activeAgentCount > 0 && (
            <div className="active-agents-badge">
              <Activity size={12} />
              <span>{activeAgentCount} 실행 중</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Main 3-Panel Layout ───────────────────── */}
      <div className="main-layout">
        {/* Left Panel: CEO Chat */}
        <ChatPanel
          messages={messages}
          onSendTask={sendTask}
          isConnected={isConnected}
        />

        {/* Center Panel: Node Graph */}
        <NodeGraph nodeData={nodeData} />

        {/* Right Panel: Agent Logs + Roster */}
        <div className="right-panel">
          <AgentLogPanel logs={agentLogs} />
          <AgentRosterPanel nodeData={nodeData} />
        </div>
      </div>

      {/* ── Status Bar ───────────────────────────── */}
      <div className="status-bar">
        <div className="status-bar-left">
          <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
          <span className="status-text">{statusText}</span>
        </div>
        <div className="status-bar-right">
          <span className="status-meta">Client: {CLIENT_ID}</span>
          <span className="status-meta">Agents: {nodeData.nodes?.length || 0}</span>
          <span className="status-meta">Logs: {agentLogs.length}</span>
        </div>
      </div>
    </div>
  );
}
