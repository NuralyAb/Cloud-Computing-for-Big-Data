from fastapi import APIRouter, HTTPException, Depends

from models import BotStatus, BotAction
from services.supabase_service import get_project
from services.bot_manager import start_bot, stop_bot, is_running
from services.conversation_service import get_analytics, get_unanswered_questions
from dependencies import get_current_user

router = APIRouter(prefix="/api/projects", tags=["bots"])


def _check_owner(project: dict, user: dict):
    if project.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Not your project")


@router.post("/{project_id}/start", response_model=BotAction)
async def start_project_bot(project_id: str, user: dict = Depends(get_current_user)):
    try:
        project = await get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        _check_owner(project, user)

        if is_running(project_id):
            return BotAction(status="already_running")

        await start_bot(
            project_id,
            project["telegram_token"],
            project["table_name"],
            project.get("owner_tg_id"),
        )
        return BotAction(status="started")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/stop", response_model=BotAction)
async def stop_project_bot(project_id: str, user: dict = Depends(get_current_user)):
    try:
        project = await get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        _check_owner(project, user)

        if not is_running(project_id):
            return BotAction(status="not_running")

        await stop_bot(project_id)
        return BotAction(status="stopped")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/status", response_model=BotStatus)
async def get_bot_status(project_id: str, user: dict = Depends(get_current_user)):
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _check_owner(project, user)
    return BotStatus(running=is_running(project_id))


@router.get("/{project_id}/analytics")
async def project_analytics(project_id: str, user: dict = Depends(get_current_user)):
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _check_owner(project, user)
    return await get_analytics(project_id)


@router.get("/{project_id}/unanswered")
async def project_unanswered(project_id: str, user: dict = Depends(get_current_user)):
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _check_owner(project, user)
    return await get_unanswered_questions(project_id)
