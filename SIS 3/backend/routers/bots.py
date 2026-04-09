from fastapi import APIRouter, HTTPException

from models import BotStatus, BotAction
from services.supabase_service import get_project
from services.bot_manager import start_bot, stop_bot, is_running

router = APIRouter(prefix="/api/projects", tags=["bots"])


@router.post("/{project_id}/start", response_model=BotAction)
async def start_project_bot(project_id: str):
    """Start the Telegram bot for a project."""
    try:
        project = await get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if is_running(project_id):
            return BotAction(status="already_running")

        await start_bot(project_id, project["telegram_token"], project["table_name"])
        return BotAction(status="started")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/stop", response_model=BotAction)
async def stop_project_bot(project_id: str):
    """Stop the Telegram bot for a project."""
    try:
        project = await get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not is_running(project_id):
            return BotAction(status="not_running")

        await stop_bot(project_id)
        return BotAction(status="stopped")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/status", response_model=BotStatus)
async def get_bot_status(project_id: str):
    """Check if the bot is running for a project."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return BotStatus(running=is_running(project_id))
