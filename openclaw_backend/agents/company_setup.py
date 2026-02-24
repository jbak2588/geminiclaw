"""
Company Setup: AI-driven organizational chart generator.
Uses company profile + product whitepaper to recommend departments.
"""
import json
import os
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings


# ──────────────────────────────────────────────
# Pre-built company profiles
# ──────────────────────────────────────────────
COMPANY_PROFILES = {
    "pt_humantric": {
        "name": "PT Humantric Net Indonesia",
        "type": "PMA (외국인 투자 법인)",
        "kbli": "63122 (포털 웹 및 소셜 미디어 플랫폼 운영)",
        "country": "Indonesia",
        "product": "Mozzy - 하이퍼로컬 커뮤니티 슈퍼앱 (29개국, 11개 기능)",
        "current_team_size": 1,
        "stage": "Pre-launch (앱스토어 등록 준비 중)",
        "whitepaper_dir": "",  # Will be set dynamically
    },
}


def _load_whitepaper(whitepaper_dir: str, max_chars: int = 5000) -> str:
    """Load whitepaper content as context (truncated)."""
    if not whitepaper_dir or not os.path.isdir(whitepaper_dir):
        return ""
    
    content_parts = []
    for filename in sorted(os.listdir(whitepaper_dir)):
        filepath = os.path.join(whitepaper_dir, filename)
        if os.path.isfile(filepath) and filename.endswith(('.md', '.txt')):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()[:max_chars]
                content_parts.append(f"--- {filename} ---\n{content}")
            except Exception:
                pass
    
    return "\n\n".join(content_parts[:3])  # Max 3 files


async def generate_org_chart(
    company_profile: Dict[str, Any],
    whitepaper_dir: str = "",
) -> Dict[str, Any]:
    """
    Generate an AI-recommended organizational chart for a company.
    
    Returns:
        {
            "company_name": "PT Humantric Net Indonesia",
            "departments": [
                {
                    "id": "legal",
                    "name": "법무/준법팀",
                    "name_en": "Legal & Compliance",
                    "emoji": "⚖️",
                    "description": "이용약관, 개인정보처리방침...",
                    "priority": "essential",
                    "agents": ["legal"],
                    "default_enabled": true
                },
                ...
            ]
        }
    """
    # Load whitepaper context
    wp_context = _load_whitepaper(whitepaper_dir) if whitepaper_dir else ""
    
    prompt = f"""You are an expert business consultant specializing in Indonesian company formation.

Analyze this company and recommend an organizational structure:

COMPANY INFO:
- Name: {company_profile.get('name', 'Unknown')}
- Type: {company_profile.get('type', 'Unknown')}
- KBLI: {company_profile.get('kbli', 'Unknown')}
- Country: {company_profile.get('country', 'Unknown')}
- Product: {company_profile.get('product', 'Unknown')}
- Current Team Size: {company_profile.get('current_team_size', 1)}
- Stage: {company_profile.get('stage', 'Unknown')}

{"PRODUCT WHITEPAPER (excerpt):" + chr(10) + wp_context if wp_context else ""}

RULES:
1. Output ONLY a valid JSON object with the structure shown below.
2. Recommend 5-8 departments appropriate for this company type, stage, and local regulations.
3. For Indonesian PMA: include departments needed for LKPM reporting, PSE registration, tax compliance.
4. Each department must have a unique "id" matching one of these agent types:
   [admin, legal, accountant, developer, marketer, cs, hr, researcher, writer]
5. Set "priority" as "essential", "important", or "optional" based on company stage.
6. Set "default_enabled" to true for essential/important departments.
7. Write department names in Korean, descriptions in Korean.

OUTPUT FORMAT:
{{
  "company_name": "{company_profile.get('name', 'Company')}",
  "departments": [
    {{
      "id": "legal",
      "name": "법무/준법팀",
      "name_en": "Legal & Compliance",
      "emoji": "⚖️",
      "description": "이용약관, 개인정보처리방침, PSE 등록, KOMINFO 규정 준수",
      "priority": "essential",
      "agents": ["legal"],
      "default_enabled": true
    }}
  ]
}}
"""

    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing.")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY,
            max_output_tokens=2048,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # Parse JSON from response (handle markdown code blocks)
        json_str = content
        if "```" in json_str:
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            json_str = json_str.strip()
        
        result = json.loads(json_str)
        return result
        
    except json.JSONDecodeError:
        # Return fallback org chart
        return _get_fallback_org_chart(company_profile)
    except Exception as e:
        return {
            "error": str(e),
            **_get_fallback_org_chart(company_profile),
        }


def _get_fallback_org_chart(profile: Dict) -> Dict:
    """Fallback org chart when AI fails."""
    return {
        "company_name": profile.get("name", "Company"),
        "departments": [
            {
                "id": "admin",
                "name": "경영/행정팀",
                "name_en": "Administration",
                "emoji": "🏛️",
                "description": "PMA 법인 유지관리, LKPM 보고, OSS/NIB 갱신",
                "priority": "essential",
                "agents": ["admin"],
                "default_enabled": True,
            },
            {
                "id": "legal",
                "name": "법무/준법팀",
                "name_en": "Legal & Compliance",
                "emoji": "⚖️",
                "description": "이용약관, 개인정보처리방침, PSE 등록",
                "priority": "essential",
                "agents": ["legal"],
                "default_enabled": True,
            },
            {
                "id": "accountant",
                "name": "회계/재무팀",
                "name_en": "Finance & Accounting",
                "emoji": "💰",
                "description": "SPT 세무신고, VAT, 법인세, 재무제표",
                "priority": "essential",
                "agents": ["accountant"],
                "default_enabled": True,
            },
            {
                "id": "developer",
                "name": "개발팀",
                "name_en": "Engineering",
                "emoji": "💻",
                "description": "앱 유지보수, PG 연동, 서버 운영",
                "priority": "essential",
                "agents": ["developer"],
                "default_enabled": True,
            },
            {
                "id": "marketer",
                "name": "마케팅/성장팀",
                "name_en": "Marketing & Growth",
                "emoji": "📢",
                "description": "ASO, 소셜미디어, 커뮤니티 시딩",
                "priority": "important",
                "agents": ["marketer"],
                "default_enabled": True,
            },
            {
                "id": "cs",
                "name": "고객 지원팀",
                "name_en": "Customer Support",
                "emoji": "🎧",
                "description": "사용자 문의, 신고 처리, FAQ",
                "priority": "important",
                "agents": ["cs"],
                "default_enabled": False,
            },
            {
                "id": "hr",
                "name": "인사팀",
                "name_en": "Human Resources",
                "emoji": "👤",
                "description": "채용, BPJS 등록, 근로계약서",
                "priority": "optional",
                "agents": ["hr"],
                "default_enabled": False,
            },
        ],
    }
