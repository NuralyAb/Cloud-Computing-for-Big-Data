from pydantic import BaseModel
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    telegram_token: str
    knowledge_base: str


class ProjectOut(BaseModel):
    id: str
    name: str
    telegram_token: str
    table_name: str
    created_at: str


class BotStatus(BaseModel):
    running: bool


class BotAction(BaseModel):
    status: str
