from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

from core.db import metadata_db

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class TeamPresetCreate(BaseModel):
    name: str
    config: List[Dict[str, Any]]

@router.get("/projects")
def list_projects():
    """List all created projects (threads)."""
    return {"projects": metadata_db.get_projects()}

@router.post("/projects")
def create_project(project: ProjectCreate):
    """Create a new project workspace."""
    project_id = str(uuid.uuid4())
    metadata_db.create_project(project_id, project.name, project.description)
    return {"id": project_id, "name": project.name, "description": project.description}

@router.get("/teams")
def list_teams():
    """List saved team presets."""
    return {"teams": metadata_db.get_team_presets()}

@router.post("/teams")
def create_team(team: TeamPresetCreate):
    """Save a new team preset configuration."""
    preset_id = str(uuid.uuid4())
    metadata_db.create_team_preset(preset_id, team.name, team.config)
    return {"id": preset_id, "name": team.name, "config": team.config}
