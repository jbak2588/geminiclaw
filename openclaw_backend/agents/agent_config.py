"""
Agent Configuration: Defines roles, team presets, and organizational structure.
Skills are loaded from SKILL.md files under SKILLS_DIR.
Falls back to hardcoded prompts if SKILL.md is missing.
"""
import os
import re
import logging
from dataclasses import dataclass
from typing import List, Dict

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Skills 파일 시스템 경로
# ──────────────────────────────────────────────
SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")


# ──────────────────────────────────────────────
# Skills 로더
# ──────────────────────────────────────────────

def load_company_context() -> str:
    """
    COMPANY.md 파일에서 회사 컨텍스트를 로드합니다.
    파일이 없으면 하드코딩된 기본값을 반환합니다.
    """
    company_file = os.path.join(SKILLS_DIR, "COMPANY.md")
    if os.path.isfile(company_file):
        try:
            with open(company_file, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info("[Skills] COMPANY.md 로드됨")
            return f"\n[COMPANY CONTEXT - 반드시 참고하세요]\n{content}\n"
        except Exception as e:
            logger.warning(f"[Skills] COMPANY.md 로드 실패: {e}")

    # Fallback: 하드코딩된 기본 컨텍스트
    return _DEFAULT_COMPANY_CONTEXT


def load_agents_context() -> str:
    """
    AGENTS.md 파일에서 팀 공통 규칙을 로드합니다.
    """
    agents_file = os.path.join(SKILLS_DIR, "AGENTS.md")
    if os.path.isfile(agents_file):
        try:
            with open(agents_file, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info("[Skills] AGENTS.md 로드됨")
            return f"\n[TEAM RULES]\n{content}\n"
        except Exception as e:
            logger.warning(f"[Skills] AGENTS.md 로드 실패: {e}")
    return ""


def load_skill(agent_name: str, fallback_prompt: str = "") -> str:
    """
    에이전트 이름에 해당하는 SKILL.md를 로드합니다.
    YAML frontmatter(---...---) 제거 후 본문만 반환합니다.
    파일이 없으면 fallback_prompt를 반환합니다.
    """
    skill_file = os.path.join(SKILLS_DIR, agent_name, "SKILL.md")
    if os.path.isfile(skill_file):
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()

            # YAML frontmatter 제거 (--- ... --- 블록)
            content = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL).strip()

            logger.info(f"[Skills] {agent_name}/SKILL.md 로드됨")
            return content
        except Exception as e:
            logger.warning(f"[Skills] {agent_name}/SKILL.md 로드 실패: {e}")

    # Fallback: 하드코딩 프롬프트
    if fallback_prompt:
        logger.info(f"[Skills] {agent_name}: SKILL.md 없음, 기본 프롬프트 사용")
    return fallback_prompt


# ──────────────────────────────────────────────
# 하드코딩 Fallback (SKILL.md 없을 때 사용)
# ──────────────────────────────────────────────
_DEFAULT_COMPANY_CONTEXT = """
[COMPANY CONTEXT - 반드시 참고하세요]
회사명: PT Humantric Net Indonesia
법인 유형: PMA (외국인 투자 법인, Penanaman Modal Asing)
국가: Indonesia
KBLI: 63122 (포털 웹 및 소셜 미디어 플랫폼 운영)
웹사이트: https://humantric.net
제품: Mozzy (모지) - AI 기반 글로벌 하이퍼로컬 커뮤니티 슈퍼앱
앱 코드 저장소: C:\\bling\\bling_app (Flutter), GitHub: https://github.com/jbak2588/bling
현재 단계: 앱 완성 (PG 연동 제외), 필드 테스트 중, 앱스토어 등록 준비

제품 핵심 기능 (11개):
1. 하이퍼로컬 중고거래 마켓플레이스
2. 구인구직 (로컬 잡 매칭)
3. 부동산 (방/집 렌트)
4. 분실물 찾기 (Lost & Found)
5. 지역 뉴스 피드
6. 경매 시스템
7. 지역 맛집 리뷰
8. 커뮤니티 게시판
9. 1:1 채팅 (Firebase)
10. AI 기반 자동 번역 (29개 언어)
11. 위치 기반 거리순 정렬

이 정보를 바탕으로 실제 문서를 작성하세요. "정보를 제공해주세요"라고 요청하지 마세요.
"""

_FALLBACK_PROMPTS = {
    "pm": (
        "You are a Project Manager Agent. Your job is to:\n"
        "1. Analyze the CTO's instruction and break it into sub-tasks.\n"
        "2. Assign each sub-task to the most appropriate team member.\n"
        "3. Be CONCISE. Output ONLY a JSON object mapping agent names to their tasks.\n"
        "4. Format: {\"agent_name\": \"task description\", ...}\n"
        "5. Only assign to agents that exist in the current team.\n"
    ),
    "developer": (
        "You are a Software Developer Agent. You can:\n"
        "1. Write, read, and modify code files using tools.\n"
        "2. Execute shell commands for builds, tests, etc.\n"
        "3. Be BRIEF and DIRECT. Provide working code, not tutorials.\n"
    ),
    "reviewer": (
        "You are a QA/Reviewer Agent. Be LENIENT and BRIEF.\n"
        "If the work reasonably addresses the task, reply ONLY with 'APPROVED'.\n"
        "Only reject if there are critical errors. If rejecting, give ONE sentence of feedback.\n"
    ),
    "legal": (
        "You are a Legal Advisor Agent for an Indonesian PMA company.\n"
        "Specialize in privacy policies, ToS, PSE registration, UU PDP.\n"
        "Write in Korean unless instructed otherwise. Be practical and concise.\n"
    ),
    "marketer": (
        "You are a Marketing Strategist Agent.\n"
        "Specialize in ASO, social media, community seeding, hyperlocal growth.\n"
        "Write in Korean unless instructed otherwise. Be data-driven.\n"
    ),
    "accountant": (
        "You are an Accountant Agent for an Indonesian PMA company.\n"
        "Specialize in SPT, VAT/PPN, PPh Badan, LKPM reports.\n"
        "Write in Korean unless instructed otherwise. Be precise with numbers.\n"
    ),
    "admin": (
        "You are an Administration Agent for an Indonesian PMA company.\n"
        "Specialize in PMA maintenance, NIB/OSS, LKPM, business licenses.\n"
        "Write in Korean unless instructed otherwise. Be thorough.\n"
    ),
    "cs": (
        "You are a Customer Support Agent for Mozzy app.\n"
        "Specialize in FAQ docs, response templates, complaint handling.\n"
        "Write in Korean unless instructed otherwise. Be empathetic and clear.\n"
    ),
    "hr": (
        "You are an HR Agent for an Indonesian PMA company.\n"
        "Specialize in PKWT/PKWTT contracts, BPJS, recruitment, labor law.\n"
        "Write in Korean unless instructed otherwise. Be precise with regulations.\n"
    ),
}


# ──────────────────────────────────────────────
# AgentConfig 데이터 클래스
# ──────────────────────────────────────────────
@dataclass
class AgentConfig:
    """Configuration for a single AI agent in the team."""
    name: str               # Unique ID: "developer", "legal", "marketer"
    role: str               # Display name: "Software Developer", "법률 담당"
    system_prompt: str      # Role-specific instructions (from SKILL.md or fallback)
    tools: List[str]        # Tool names this agent can use
    knowledge_dir: str = "" # Path to folder with reference documents


# ──────────────────────────────────────────────
# All available agent roles
# SKILL.md 파일에서 system_prompt 로드, 없으면 Fallback
# ──────────────────────────────────────────────

AVAILABLE_ROLES: Dict[str, AgentConfig] = {
    "pm": AgentConfig(
        name="pm",
        role="👔 PM (Project Manager)",
        system_prompt=load_skill("pm", _FALLBACK_PROMPTS["pm"]),
        tools=[],
    ),
    "developer": AgentConfig(
        name="developer",
        role="💻 개발팀 (Engineering)",
        system_prompt=load_skill("developer", _FALLBACK_PROMPTS["developer"]),
        tools=["read_file", "write_file", "execute_shell_command"],
    ),
    "reviewer": AgentConfig(
        name="reviewer",
        role="✅ 품질검수 (QA/Reviewer)",
        system_prompt=load_skill("reviewer", _FALLBACK_PROMPTS["reviewer"]),
        tools=["read_file"],
    ),
    "legal": AgentConfig(
        name="legal",
        role="⚖️ 법무/준법팀 (Legal & Compliance)",
        system_prompt=load_skill("legal", _FALLBACK_PROMPTS["legal"]),
        tools=["read_file", "write_file"],
    ),
    "marketer": AgentConfig(
        name="marketer",
        role="📢 마케팅/성장팀 (Marketing & Growth)",
        system_prompt=load_skill("marketer", _FALLBACK_PROMPTS["marketer"]),
        tools=["read_file", "write_file"],
    ),
    "accountant": AgentConfig(
        name="accountant",
        role="💰 회계/재무팀 (Finance & Accounting)",
        system_prompt=load_skill("accountant", _FALLBACK_PROMPTS["accountant"]),
        tools=["read_file", "write_file"],
    ),
    "admin": AgentConfig(
        name="admin",
        role="🏛️ 경영/행정팀 (Administration)",
        system_prompt=load_skill("admin", _FALLBACK_PROMPTS["admin"]),
        tools=["read_file", "write_file"],
    ),
    "cs": AgentConfig(
        name="cs",
        role="🎧 고객 지원팀 (Customer Support)",
        system_prompt=load_skill("cs", _FALLBACK_PROMPTS["cs"]),
        tools=["read_file", "write_file"],
    ),
    "hr": AgentConfig(
        name="hr",
        role="👤 인사팀 (Human Resources)",
        system_prompt=load_skill("hr", _FALLBACK_PROMPTS["hr"]),
        tools=["read_file", "write_file"],
    ),
}


# ──────────────────────────────────────────────
# Team Presets: Pre-configured department groups
# ──────────────────────────────────────────────

TEAM_PRESETS = {
    "startup_minimum": {
        "name": "🚀 스타트업 최소 구성",
        "description": "1인 창업자를 위한 필수 팀 (법무 + 개발 + 회계)",
        "agents": ["developer", "legal", "accountant"],
    },
    "pre_launch": {
        "name": "📱 앱 출시 준비팀",
        "description": "앱스토어 등록 전 필요한 팀 구성",
        "agents": ["developer", "legal", "marketer", "accountant"],
    },
    "full_company": {
        "name": "🏢 정식 법인 운영",
        "description": "PMA 법인의 전체 부서 구성",
        "agents": ["admin", "legal", "accountant", "developer", "marketer", "cs", "hr"],
    },
    "growth_team": {
        "name": "📈 성장 집중팀",
        "description": "마케팅 + 고객지원 중심의 성장 팀",
        "agents": ["marketer", "cs", "developer"],
    },
    "compliance_team": {
        "name": "📋 준법/행정 팀",
        "description": "법인 유지관리와 규정 준수를 위한 팀",
        "agents": ["admin", "legal", "accountant", "hr"],
    },
}

# ──────────────────────────────────────────────
# 런타임에 COMPANY_CONTEXT 공급 (agent_factory.py에서 사용)
# ──────────────────────────────────────────────
COMPANY_CONTEXT = load_company_context()
AGENTS_CONTEXT = load_agents_context()
