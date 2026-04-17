import { useMemo } from 'react';
import { Users, Wrench } from 'lucide-react';

/**
 * 백엔드 agent_config.py의 AVAILABLE_ROLES를 미러링.
 * 향후 REST API(/api/agents)로 동적 로드 가능.
 */
const ALL_AGENTS = [
  { name: 'pm',         emoji: '👔', role: 'PM (Project Manager)',           tools: 0,  group: 'core'    },
  { name: 'developer',  emoji: '💻', role: '개발팀 (Engineering)',            tools: 3,  group: 'core'    },
  { name: 'reviewer',   emoji: '✅', role: '품질검수 (QA/Reviewer)',          tools: 1,  group: 'core'    },
  { name: 'designer',   emoji: '🎨', role: '디자인 (UI/UX)',                  tools: 1,  group: 'product' },
  { name: 'legal',      emoji: '⚖️', role: '법무/준법 (Legal)',               tools: 2,  group: 'biz'     },
  { name: 'marketer',   emoji: '📢', role: '마케팅/성장 (Marketing)',          tools: 2,  group: 'biz'     },
  { name: 'accountant', emoji: '💰', role: '회계/재무 (Finance)',              tools: 2,  group: 'biz'     },
  { name: 'admin',      emoji: '🏛️', role: '경영/행정 (Admin)',               tools: 2,  group: 'biz'     },
  { name: 'cs',         emoji: '🎧', role: '고객지원 (Support)',               tools: 2,  group: 'ops'     },
  { name: 'hr',         emoji: '👤', role: '인사 (HR)',                        tools: 2,  group: 'ops'     },
  { name: 'researcher', emoji: '🔍', role: '리서치 (Research)',                tools: 1,  group: 'product' },
  { name: 'analyst',    emoji: '📊', role: '분석 (Analyst)',                   tools: 1,  group: 'product' },
];

const GROUP_LABELS = {
  core:    '핵심 팀',
  product: '프로덕트',
  biz:     '경영 지원',
  ops:     '운영',
};

const GROUP_ORDER = ['core', 'product', 'biz', 'ops'];

function AgentCard({ agent, status }) {
  const isActive  = status === 'running';
  const isDone    = status === 'completed' || status === 'done';
  const isInTeam  = status != null;

  return (
    <div className={`roster-card ${isActive ? 'active' : ''} ${isDone ? 'done' : ''} ${isInTeam ? 'in-team' : ''}`}>
      <div className="roster-card-emoji">{agent.emoji}</div>
      <div className="roster-card-info">
        <span className="roster-card-name">{agent.name}</span>
        <span className="roster-card-role">{agent.role}</span>
      </div>
      {isActive && <div className="roster-pulse" />}
      <div className="roster-card-status">
        {isActive  && <span className="roster-status running">실행 중</span>}
        {isDone    && <span className="roster-status done">완료</span>}
        {!isInTeam && <span className="roster-status idle">대기</span>}
        {isInTeam && !isActive && !isDone && <span className="roster-status queued">대기열</span>}
      </div>
    </div>
  );
}

export default function AgentRosterPanel({ nodeData }) {
  // nodeData.nodes에서 현재 활성 에이전트 상태 맵 생성
  const agentStatusMap = useMemo(() => {
    const map = {};
    if (nodeData?.nodes) {
      nodeData.nodes.forEach(n => {
        map[n.id || n.name] = n.status;
      });
    }
    return map;
  }, [nodeData]);

  const groups = useMemo(() => {
    return GROUP_ORDER.map(gid => ({
      id: gid,
      label: GROUP_LABELS[gid],
      agents: ALL_AGENTS.filter(a => a.group === gid),
    }));
  }, []);

  const activeCount = Object.values(agentStatusMap).filter(s => s === 'running').length;
  const totalInTeam = Object.keys(agentStatusMap).length;

  return (
    <div className="roster-panel">
      {/* Header */}
      <div className="panel-header roster-header">
        <div className="panel-header-icon">
          <Users size={14} />
        </div>
        <span>에이전트 로스터</span>
        <div className="roster-badge-group">
          <span className="roster-badge total">{ALL_AGENTS.length}명</span>
          {totalInTeam > 0 && (
            <span className="roster-badge active">{activeCount > 0 ? `${activeCount} 실행` : `${totalInTeam} 배치`}</span>
          )}
        </div>
      </div>

      {/* Agent Grid */}
      <div className="roster-content">
        {groups.map(g => (
          <div key={g.id} className="roster-group">
            <div className="roster-group-label">{g.label}</div>
            <div className="roster-grid">
              {g.agents.map(agent => (
                <AgentCard
                  key={agent.name}
                  agent={agent}
                  status={agentStatusMap[agent.name]}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
