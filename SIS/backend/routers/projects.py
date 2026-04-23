import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from slugify import slugify

from models import ProjectOut
from services.chunker import chunk_text
from services.embedder import embed_texts
from services.text_extractor import extract_from_file, extract_from_url
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
from dependencies import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _check_owner(project: dict, user: dict):
    if project.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Not your project")


@router.post("", response_model=ProjectOut)
async def create_project(
    name: str = Form(...),
    telegram_token: str = Form(...),
    source_type: str = Form("text"),
    knowledge_base: str | None = Form(None),
    source_url: str | None = Form(None),
    owner_tg_id: int | None = Form(None),
    file: UploadFile | None = File(None),
    user: dict = Depends(get_current_user),
):
    """Create a new project. Knowledge base source: text | file | url."""
    try:
        # Extract knowledge base text
        kb_text = ""
        if source_type == "text":
            kb_text = (knowledge_base or "").strip()
        elif source_type == "file":
            if not file:
                raise HTTPException(status_code=400, detail="File is required")
            data = await file.read()
            kb_text = extract_from_file(file.filename, data)
        elif source_type == "url":
            if not source_url:
                raise HTTPException(status_code=400, detail="URL is required")
            kb_text = await extract_from_url(source_url)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source_type: {source_type}")

        if not kb_text or len(kb_text) < 20:
            raise HTTPException(status_code=400, detail="Knowledge base text is too short or empty")

        project_id = str(uuid.uuid4())
        short_id = uuid.uuid4().hex[:8]
        table_name = "kb_" + slugify(name, separator="_") + "_" + short_id

        await create_kb_table(table_name)

        chunks = chunk_text(kb_text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Failed to chunk knowledge base")

        texts = [c["text"] for c in chunks]
        embeddings = await embed_texts(texts)
        await insert_chunks(table_name, chunks, embeddings)

        record = await create_project_record(
            project_id, name, telegram_token, table_name, user["id"], owner_tg_id
        )

        return ProjectOut(
            id=record["id"],
            name=record["name"],
            telegram_token=record["telegram_token"],
            table_name=record["table_name"],
            created_at=record["created_at"],
            owner_tg_id=record.get("owner_tg_id"),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ProjectOut])
async def list_projects(user: dict = Depends(get_current_user)):
    try:
        projects = await get_all_projects(user["id"])
        return [
            ProjectOut(
                id=p["id"],
                name=p["name"],
                telegram_token=p["telegram_token"],
                table_name=p["table_name"],
                created_at=p["created_at"],
                owner_tg_id=p.get("owner_tg_id"),
            )
            for p in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectOut)
async def get_single_project(project_id: str, user: dict = Depends(get_current_user)):
    try:
        project = await get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        _check_owner(project, user)
        return ProjectOut(
            id=project["id"],
            name=project["name"],
            telegram_token=project["telegram_token"],
            table_name=project["table_name"],
            created_at=project["created_at"],
            owner_tg_id=project.get("owner_tg_id"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    try:
        project = await get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        _check_owner(project, user)

        if is_running(project_id):
            await stop_bot(project_id)

        await drop_kb_table(project["table_name"])
        await delete_project_record(project_id)

        return {"detail": "Project deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
