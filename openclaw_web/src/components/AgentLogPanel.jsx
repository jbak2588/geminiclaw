import { useRef, useEffect } from 'react';
import { Terminal } from 'lucide-react';

const STATUS_COLORS = {
  running:   '#3b82f6',
  completed: '#22c55e',
  error:     '#ef4444',
  info:      '#94a3b8',
  approval:  '#f59e0b',
  done:      '#22c55e',
  unknown:   '#64748b',
};

const STATUS_ICONS = {
  running:   '▶',
  completed: '✓',
  error:     '✕',
  info:      'ℹ',
  approval:  '⚠',
  done:      '✓',
};

function LogEntry({ entry }) {
  const color = STATUS_COLORS[entry.status] || STATUS_COLORS.unknown;
  const icon = STATUS_ICONS[entry.status] || '·';

  return (
    <div className="log-entry">
      <span className="log-time">{entry.time}</span>
      <span className="log-icon" style={{ color }}>{icon}</span>
      <span className="log-node" style={{ color }}>[{entry.node}]</span>
      <span className="log-message">{entry.message}</span>
    </div>
  );
}

export default function AgentLogPanel({ logs }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="log-panel">
      {/* Header */}
      <div className="panel-header">
        <div className="panel-header-icon">
          <Terminal size={14} />
        </div>
        <span>에이전트 로그</span>
        <span className="log-count">{logs.length}개</span>
      </div>

      {/* Log content */}
      <div className="log-content">
        {logs.length === 0 ? (
          <div className="log-empty">
            <Terminal size={24} className="empty-icon" />
            <p>로그 대기 중...</p>
          </div>
        ) : (
          logs.map(entry => <LogEntry key={entry.id} entry={entry} />)
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
