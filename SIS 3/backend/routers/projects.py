import uuid
from fastapi import APIRouter, HTTPException
from slugify import slugify

from models import ProjectCreate, ProjectOut
from services.chunker import chunk_text
from services.embedder import embed_texts
from services.supabase_service import (
    create_project_record,
    get_all_projects,
    get_project,
    delete_project as delete_project_record,
    create_kb_table,
    drop_kb_table,
    insert_chunks,
)
from services.bot_manager import stop_bot, is_running

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectOut)
async def create_project(body: ProjectCreate):
    """Create a new project: chunk text, embed, store in Supabase."""
    try:
        project_id = str(uuid.uuid4())
        short_id = uuid.uuid4().hex[:8]
        table_name = "kb_" + slugify(body.name, separator="_") + "_" + short_id

        # Create KB table
        await create_kb_table(table_name)

        # Chunk the knowledge base
        chunks = chunk_text(body.knowledge_base)
        if not chunks:
            raise HTTPException(status_code=400, detail="Knowledge base text is too short or empty.")

        # Generate embeddings
        texts = [c["text"] for c in chunks]
        embeddings = await embed_texts(texts)

        # Store chunks with embeddings
        await insert_chunks(table_name, chunks, embeddings)

        # Save project record
        record = await create_project_record(project_id, body.name, body.telegram_token, table_name)

        return ProjectOut(
            id=record["id"],
            name=record["name"],
            telegram_token=record["telegram_token"],
            table_name=record["table_name"],
            created_at=record["created_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ProjectOut])
async def list_projects():
    """List all projects."""
    try:
        projects = await get_all_projects()
        return [
            ProjectOut(
                id=p["id"],
                name=p["name"],
                telegram_token=p["telegram_token"],
                table_name=p["table_name"],
                created_at=p["created_at"],
            )
            for p in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectOut)
async def get_single_project(project_id: str):
    """Get a single project by ID."""
    try:
        project = await get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectOut(
            id=project["id"],
            name=project["name"],
            telegram_token=project["telegram_token"],
            table_name=project["table_name"],
            created_at=project["created_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project: stop bot, drop KB table, remove record."""
    try:
        project = await get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Stop bot if running
        if is_running(project_id):
            await stop_bot(project_id)

        # Drop KB table
        await drop_kb_table(project["table_name"])

        # Delete project record
        await delete_project_record(project_id)

        return {"detail": "Project deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
