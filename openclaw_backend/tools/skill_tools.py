import os
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from core.config import settings

@tool
def update_skill_manual(role_name: str, new_instruction: str, project_id: str) -> str:
    """Read the current skill manual for a role, inject a new instruction or feedback seamlessly using an LLM, and overwrite the manual file.
    Args:
        role_name: The name of the role (e.g., 'pm', 'developer', 'marketer').
        new_instruction: The new feedback or instruction from the CTO to add to the manual.
        project_id: The project ID.
    Returns:
        A success or error message.
    """
    skill_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "storage", "skills", project_id, f"{role_name}_manual.md"
    )

    if not os.path.exists(skill_path):
        return f"Error: Skill manual for {role_name} in project {project_id} does not exist at {skill_path}."

    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        if not settings.GEMINI_API_KEY:
            return "Error: GEMINI_API_KEY is not set."

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY,
            max_output_tokens=4096,
        )

        sys_prompt = (
            "You are an expert AI operation engineer. Your task is to update a role's Skill Manual (Markdown) based on new CTO feedback.\n"
            "Rules:\n"
            "1. Seamlessly integrate the new instruction into the existing Markdown structure.\n"
            "2. Keep the original intent and responsibilities, just append or modify the relevant sections to reflect the new rule.\n"
            "3. Return ONLY the raw Markdown content. Do not include markdown code blocks ```markdown ... ``` around your output, just the raw text.\n"
            "4. Maintain a professional, clear, and actionable tone."
        )

        user_prompt = f"Current Skill Manual:\n{current_content}\n\nCTO Feedback/New Instruction:\n{new_instruction}\n\nPlease output the updated Markdown manual."

        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ])

        new_content = response.content.strip()

        # Clean up any accidental markdown blocks
        if new_content.startswith("```markdown"):
            new_content = new_content[11:]
        if new_content.startswith("```"):
            new_content = new_content[3:]
        if new_content.endswith("```"):
            new_content = new_content[:-3]
        
        new_content = new_content.strip()

        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"Successfully updated {role_name}_manual.md in project {project_id} with the new instructions."

    except Exception as e:
        return f"Error updating skill manual: {str(e)}"
