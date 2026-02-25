"""Skills 파일 시스템 로드 검증 스크립트"""
import os
import re

SKILLS_DIR = r"E:\geminiclaw\skills"


def load_skill(agent_name):
    skill_file = os.path.join(SKILLS_DIR, agent_name, "SKILL.md")
    if os.path.isfile(skill_file):
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL).strip()
        return content
    return None


agents = ["pm", "developer", "reviewer", "legal", "marketer", "accountant", "admin", "cs", "hr"]
print("=== Skills 로드 검증 ===")
all_ok = True
for a in agents:
    result = load_skill(a)
    if result:
        print(f"  [OK] {a}: {len(result)}자 로드됨")
    else:
        print(f"  [FAIL] {a}: SKILL.md 없음")
        all_ok = False

company = os.path.join(SKILLS_DIR, "COMPANY.md")
agents_f = os.path.join(SKILLS_DIR, "AGENTS.md")
print(f"  [OK] COMPANY.md: {os.path.getsize(company)}bytes" if os.path.isfile(company) else "  [FAIL] COMPANY.md 없음")
print(f"  [OK] AGENTS.md: {os.path.getsize(agents_f)}bytes" if os.path.isfile(agents_f) else "  [FAIL] AGENTS.md 없음")
print("\n결과:", "✅ ALL PASS" if all_ok else "❌ SOME FAILED")
