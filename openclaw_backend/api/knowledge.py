from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import os
import io
from pypdf import PdfReader
import json
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from core.config import settings, sanitize_project_id
from core.db import metadata_db

router = APIRouter()

def parse_pdf_and_extract_metadata(pdf_bytes: bytes, filename: str) -> dict:
    """Extract text from PDF and use Gemini to generate Markdown and Metadata."""
    try:
        # Extract raw text
        reader = PdfReader(io.BytesIO(pdf_bytes))
        raw_text = ""
        for page in reader.pages:
            raw_text += page.extract_text() + "\n\n"
            
        if not raw_text.strip():
            raise ValueError("No extractable text found in PDF.")

        # Call Gemini to format and extract metadata
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY,
            max_output_tokens=8192,
        )

        sys_prompt = (
            "You are an expert document parser. "
            "Your task is to convert raw OCR or PDF text into clean, structured Markdown, "
            "and also extract metadata (Title, Summary, Table of Contents). "
            "Return the result EXACTLY as a JSON object with two keys: "
            "1) 'metadata': an object containing 'title' (string), 'summary' (short paragraph), and 'toc' (string, markdown bullet list). "
            "2) 'markdown_content': the full, cleaned, formatted markdown content of the document. "
            "Do not return markdown blocks outside the JSON."
        )

        user_prompt = f"Filename: {filename}\n\nRaw Text:\n{raw_text[:30000]}" # Limit to 30k chars for safety

        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ])

        content = response.content.strip()
        
        # Clean up JSON wrapper if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        result = json.loads(content.strip())
        return result

    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


@router.post("/{project_id}/knowledge")
async def upload_knowledge_document(
    project_id: str,
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Sanitize project_id to prevent path traversal
    project_id = sanitize_project_id(project_id)
        
    try:
        pdf_bytes = await file.read()
        
        # 1. Parse and extract
        parsed_data = parse_pdf_and_extract_metadata(pdf_bytes, file.filename)
        metadata = parsed_data.get("metadata", {})
        markdown_content = parsed_data.get("markdown_content", "")
        
        # 2. Save Markdown to disk
        doc_id = str(uuid.uuid4())
        safe_filename = f"{doc_id}.md"
        storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "knowledge", project_id)
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, safe_filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        # 3. Save Metadata to DB
        metadata_db.create_knowledge_document(
            doc_id=doc_id,
            project_id=project_id,
            title=metadata.get("title", file.filename),
            summary=metadata.get("summary", "No summary available."),
            toc=metadata.get("toc", ""),
            file_path=file_path
        )
        
        return {"status": "success", "doc_id": doc_id, "title": metadata.get("title")}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge")
async def get_all_knowledge_documents():
    """Get a global list of all knowledge document metadata."""
    try:
        docs = metadata_db.get_knowledge_documents()
        return {"documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/knowledge")
async def get_project_knowledge_documents(project_id: str):
    """Get knowledge document metadata for a specific project."""
    try:
        docs = metadata_db.get_knowledge_documents(project_id)
        return {"documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
