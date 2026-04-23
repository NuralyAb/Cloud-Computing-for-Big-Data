from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    telegram_token: str
    knowledge_base: str
    owner_tg_id: int | None = None


class ProjectOut(BaseModel):
    id: str
    name: str
    telegram_token: str
    table_name: str
    created_at: str
    owner_tg_id: int | None = None


class BotStatus(BaseModel):
    running: bool


class BotAction(BaseModel):
    status: str
