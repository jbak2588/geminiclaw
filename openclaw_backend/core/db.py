import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)
DB_PATH = os.path.join(STORAGE_DIR, "metadata.db")

def _init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_presets (
                id TEXT PRIMARY KEY,
                name TEXT,
                config_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                title TEXT,
                summary TEXT,
                toc TEXT,
                file_path TEXT,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

_init_db()

class MetadataDB:
    @staticmethod
    def get_projects() -> List[Dict[str, str]]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description FROM projects")
            return [{"id": row[0], "name": row[1], "description": row[2]} for row in cursor.fetchall()]
            
    @staticmethod
    def create_project(project_id: str, name: str, description: str):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO projects (id, name, description) VALUES (?, ?, ?)", (project_id, name, description))
            conn.commit()
            
    @staticmethod
    def get_team_presets() -> List[Dict[str, Any]]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, config_json FROM team_presets")
            return [{"id": row[0], "name": row[1], "config": json.loads(row[2])} for row in cursor.fetchall()]

    @staticmethod
    def create_team_preset(preset_id: str, name: str, config: List[Dict[str, Any]]):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO team_presets (id, name, config_json) VALUES (?, ?, ?)", (preset_id, name, json.dumps(config)))
            conn.commit()

    @staticmethod
    def get_knowledge_documents(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("SELECT id, project_id, title, summary, toc, file_path, uploaded_at FROM knowledge_documents WHERE project_id = ? ORDER BY uploaded_at DESC", (project_id,))
            else:
                cursor.execute("SELECT id, project_id, title, summary, toc, file_path, uploaded_at FROM knowledge_documents ORDER BY uploaded_at DESC")
            
            return [{
                "id": row[0],
                "project_id": row[1],
                "title": row[2],
                "summary": row[3],
                "toc": row[4],
                "file_path": row[5],
                "uploaded_at": row[6]
            } for row in cursor.fetchall()]

    @staticmethod
    def create_knowledge_document(doc_id: str, project_id: str, title: str, summary: str, toc: str, file_path: str):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO knowledge_documents (id, project_id, title, summary, toc, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (doc_id, project_id, title, summary, toc, file_path))
            conn.commit()
            
metadata_db = MetadataDB()
