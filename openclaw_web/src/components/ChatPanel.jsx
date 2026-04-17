import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Briefcase, CheckCircle } from 'lucide-react';

const DEFAULT_TEAMS = [
  { id: 'startup',    label: '🚀 스타트업',   desc: '개발+법무+회계',         config: [{ name: 'pm' }, { name: 'developer' }, { name: 'legal' }, { name: 'accountant' }, { name: 'reviewer' }] },
  { id: 'pre_launch', label: '📱 출시 준비',   desc: '개발+법무+마케팅+회계',   config: [{ name: 'pm' }, { name: 'developer' }, { name: 'legal' }, { name: 'marketer' }, { name: 'accountant' }, { name: 'reviewer' }] },
  { id: 'full',       label: '🏢 전체 법인',   desc: '전체 7개 부서',           config: [{ name: 'pm' }, { name: 'admin' }, { name: 'legal' }, { name: 'accountant' }, { name: 'developer' }, { name: 'marketer' }, { name: 'cs' }, { name: 'hr' }, { name: 'reviewer' }] },
  { id: 'growth',     label: '📈 성장팀',      desc: '마케팅+CS+개발',          config: [{ name: 'pm' }, { name: 'marketer' }, { name: 'cs' }, { name: 'developer' }, { name: 'reviewer' }] },
  { id: 'compliance', label: '📋 준법팀',      desc: '행정+법무+회계+HR',       config: [{ name: 'pm' }, { name: 'admin' }, { name: 'legal' }, { name: 'accountant' }, { name: 'hr' }, { name: 'reviewer' }] },
];

const ROLE_COLOR = {
  pm: '#4fc3f7',
  developer: '#81c784',
  reviewer: '#ffb74d',
  designer: '#ce93d8',
  researcher: '#80deea',
  analyst: '#fff176',
  system: '#888',
};

function AgentBubble({ msg }) {
  const color = ROLE_COLOR[msg.node] || '#aaa';
  return (
    <div className="chat-bubble agent" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="bubble-avatar" style={{ background: color + '22' }}>
        {msg.status === 'approved'
          ? <CheckCircle size={12} color={color} />
          : <Bot size={12} color={color} />}
      </div>
      <div className="bubble-content" style={{ flex: 1, minWidth: 0 }}>
        <span className="bubble-role" style={{ color }}>{msg.agentName}</span>
        <pre className="bubble-text agent-text">{msg.content}</pre>
      </div>
    </div>
  );
}

export default function ChatPanel({ messages, onSendTask, isConnected }) {
  const [input, setInput] = useState('');
  const [selectedTeam, setSelectedTeam] = useState(DEFAULT_TEAMS[0]);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || !isConnected) return;
    onSendTask(trimmed, selectedTeam.config);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="panel-header">
        <div className="panel-header-icon"><User size={14} /></div>
        <span>CEO 지시 채널</span>
        <div className={`connection-dot ${isConnected ? 'connected' : 'disconnected'}`} />
      </div>

      {/* Team Selector */}
      <div className="team-selector">
        {DEFAULT_TEAMS.map(t => (
          <button
            key={t.id}
            className={`team-btn ${selectedTeam.id === t.id ? 'active' : ''}`}
            onClick={() => setSelectedTeam(t)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <Briefcase size={32} className="empty-icon" />
            <p>안녕하세요, CEO님</p>
            <p className="empty-sub">팀에게 지시사항을 입력하세요</p>
          </div>
        )}
        {messages.map(msg => {
          if (msg.role === 'agent') return <AgentBubble key={msg.id} msg={msg} />;
          return (
            <div key={msg.id} className={`chat-bubble ${msg.role}`}>
              <div className="bubble-avatar">
                {msg.role === 'ceo' ? <User size={12} /> : <Bot size={12} />}
              </div>
              <div className="bubble-content">
                <span className="bubble-role">
                  {msg.role === 'ceo' ? 'CEO' : 'System'}
                </span>
                <p className="bubble-text">{msg.content}</p>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <textarea
          className="chat-textarea"
          placeholder={isConnected ? '팀에게 지시사항을 입력하세요...' : '백엔드 연결 중...'}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!isConnected}
          rows={3}
        />
        <button
          className={`send-btn ${(!input.trim() || !isConnected) ? 'disabled' : ''}`}
          onClick={handleSend}
          disabled={!input.trim() || !isConnected}
        >
          <Send size={16} />
          <span>실행</span>
        </button>
      </div>
    </div>
  );
}
