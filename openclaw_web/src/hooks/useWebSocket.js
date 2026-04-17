import { useState, useEffect, useRef } from 'react';

const WS_URL = 'ws://localhost:8000/ws';

const CHAT_AGENTS = new Set([
  'pm', 'developer', 'reviewer', 'designer',
  'researcher', 'analyst', 'legal', 'marketer', 'accountant',
]);

const AGENT_LABELS = {
  pm: '🧠 CTO (PM)',
  developer: '👨‍💻 개발자',
  reviewer: '✅ 리뷰어',
  designer: '🎨 디자이너',
  researcher: '🔍 리서처',
  analyst: '📊 애널리스트',
  legal: '⚖️ 법무',
  marketer: '📢 마케터',
  accountant: '💰 회계',
  system: 'System',
};

export function useWebSocket(clientId) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages]     = useState([]);
  const [agentLogs, setAgentLogs]   = useState([]);
  const [nodeData, setNodeData]     = useState({ nodes: [], edges: [], active_node: null });
  const [statusText, setStatusText] = useState('연결 대기 중...');

  const ws        = useRef(null);
  const timer     = useRef(null);
  const clientRef = useRef(clientId);

  // Keep clientRef in sync (avoids stale closure)
  clientRef.current = clientId;

  useEffect(() => {
    function connect() {
      if (ws.current &&
          (ws.current.readyState === WebSocket.OPEN ||
           ws.current.readyState === WebSocket.CONNECTING)) {
        return;
      }

      const socket = new WebSocket(`${WS_URL}/${clientRef.current}`);
      ws.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        setStatusText('백엔드 연결됨');
        if (timer.current) { clearTimeout(timer.current); timer.current = null; }
      };

      socket.onclose = () => {
        setIsConnected(false);
        setStatusText('연결 끊김 – 재연결 중...');
        if (!timer.current) {
          timer.current = setTimeout(() => {
            timer.current = null;
            connect();
          }, 3000);
        }
      };

      socket.onerror = () => {
        setStatusText('연결 오류');
      };

      socket.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);

          if (payload.type === 'node_update') {
            setNodeData({
              nodes: payload.nodes || [],
              edges: payload.edges || [],
              active_node: payload.active_node,
            });

          } else if (payload.type === 'agent_event') {
            const { node, status, message } = payload;
            if (message) {
              setAgentLogs(prev => [...prev.slice(-300), {
                id: Date.now() + Math.random(),
                node, status, message,
                time: new Date().toLocaleTimeString(),
              }]);
              if (CHAT_AGENTS.has(node) && message.length > 5) {
                setMessages(prev => [...prev, {
                  id: Date.now() + Math.random(),
                  role: 'agent',
                  agentName: AGENT_LABELS[node] || node,
                  node, status, content: message,
                }]);
              }
            }
            setStatusText(`[${AGENT_LABELS[node] || node}] ${status}`);

          } else if (payload.type === 'kanban_update') {
            const inProgress = payload.tasks?.find(t => t.status === 'in_progress');
            if (inProgress) setStatusText(`진행 중: ${inProgress.agent}`);

          } else if (payload.type === 'info') {
            setStatusText(payload.message);
            setAgentLogs(prev => [...prev.slice(-300), {
              id: Date.now() + Math.random(),
              node: 'system', status: 'info',
              message: payload.message,
              time: new Date().toLocaleTimeString(),
            }]);
            setMessages(prev => [...prev, {
              id: Date.now() + Math.random(),
              role: 'system',
              content: payload.message,
            }]);

          } else if (payload.type === 'approval_request') {
            setAgentLogs(prev => [...prev.slice(-300), {
              id: Date.now() + Math.random(),
              node: 'system', status: 'approval',
              message: `승인 요청: ${payload.command}`,
              time: new Date().toLocaleTimeString(),
            }]);
          }
        } catch (err) {
          console.error('[WS] parse error:', err);
        }
      };
    }

    connect();

    return () => {
      if (timer.current) clearTimeout(timer.current);
      if (ws.current) ws.current.close();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // ← intentionally empty: connect once on mount

  function sendTask(task, teamConfig) {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      console.warn('[WS] Not connected');
      return;
    }
    ws.current.send(JSON.stringify({
      type: 'task',
      task,
      team: teamConfig,
      thread_id: clientRef.current,
    }));
    setMessages(prev => [...prev, {
      id: Date.now() + Math.random(),
      role: 'ceo',
      content: task,
    }]);
    setStatusText('에이전트 팀 가동 중...');
    setNodeData({ nodes: [], edges: [], active_node: null });
    setAgentLogs([]);
  }

  return { isConnected, messages, agentLogs, nodeData, statusText, sendTask };
}
