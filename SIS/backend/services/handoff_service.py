import httpx


async def notify_owner(bot_token: str, owner_tg_id: int, username: str | None, question: str) -> None:
    """Send a handoff notification to the project owner via the same Telegram bot."""
    user_label = f"@{username}" if username else "user"
    text = (
        f"⚠️ Бот не смог ответить\n\n"
        f"Клиент: {user_label}\n"
        f"Вопрос: {question}\n\n"
        f"Подключись и ответь лично."
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json={"chat_id": owner_tg_id, "text": text})
    except Exception:
        pass
