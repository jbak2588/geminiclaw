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


# Storage path for dynamically generated skills
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
SKILLS_DIR = os.path.join(STORAGE_DIR, "skills")
os.makedirs(SKILLS_DIR, exist_ok=True)


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
    company_description: str,
    project_id: str = "default",
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
    
    prompt = f"""You are an expert business consultant.

Analyze this company description and recommend an organizational structure:

COMPANY DESCRIPTION:
{company_description}

{"PRODUCT WHITEPAPER (excerpt):" + chr(10) + wp_context if wp_context else ""}

RULES:
1. Output ONLY a valid JSON object with the structure shown below.
2. Recommend 3-6 departments appropriate for this specific company.
3. Each department must have a unique "id" matching one of these agent types:
   [pm, admin, legal, accountant, developer, marketer, cs, hr]
4. Set "priority" as "essential", "important", or "optional".
5. Set "default_enabled" to true for essential/important departments.
6. Write department names in Korean, descriptions in Korean.

OUTPUT FORMAT:
{{
  "company_name": "Generated Company Name",
  "departments": [
    {{
      "id": "marketer",
      "name": "마케팅팀",
      "name_en": "Marketing",
      "emoji": "📢",
      "description": "SNS 채널 관리 및 콘텐츠 배포",
      "priority": "essential",
      "agents": ["marketer"],
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
        
        # Trigger async skill generation in the background (or await it)
        await generate_skill_manuals(company_description, result.get("departments", []), project_id)
        
        return result
        
    except json.JSONDecodeError:
        return _get_fallback_org_chart()
    except Exception as e:
        return {
            "error": str(e),
            **_get_fallback_org_chart(),
        }

async def generate_skill_manuals(company_description: str, departments: List[Dict], project_id: str):
    """Generate Markdown skill manuals for each active department."""
    if not settings.GEMINI_API_KEY:
        return
        
    project_skill_dir = os.path.join(SKILLS_DIR, project_id)
    os.makedirs(project_skill_dir, exist_ok=True)
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        api_key=settings.GEMINI_API_KEY,
        max_output_tokens=2048,
    )
    
    for dept in departments:
        role_id = dept.get("id")
        if not role_id:
            continue
            
        file_path = os.path.join(project_skill_dir, f"{role_id}_manual.md")
        
        # Skip if manual already exists
        if os.path.exists(file_path):
            continue
            
        prompt = f"""You are setting up the Standard Operating Procedure (SOP) for this company.

COMPANY DESCRIPTION:
{company_description}

ROLE TO DEFINE: {dept.get('name')} ({role_id})
ROLE DESCRIPTION: {dept.get('description')}

Write a concise, professional Markdown manual that this AI agent must follow when executing tasks.
Include:
1. Role Definition & Core Objective
2. Key Responsibilities
3. Output Format & Guidelines (e.g., tone of voice, specific formats)
4. Constraints or Rules

Output strictly Markdown text. NO backticks enclosing the entire response. Start directly with `# {dept.get('name')} Operating Manual`
"""
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.content.strip())
        except Exception:
            pass


def _get_fallback_org_chart() -> Dict:
    """Fallback org chart when AI fails."""
    return {
        "company_name": "My Company",
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
