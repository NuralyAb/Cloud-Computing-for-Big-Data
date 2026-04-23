import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from services.rag import retrieve, generate
from services.conversation_service import log_conversation, is_unanswered
from services.handoff_service import notify_owner

running_bots: dict[str, asyncio.Task] = {}
bot_applications: dict[str, Application] = {}


async def _start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! Ask me anything about my knowledge base.")


def _make_message_handler(project_id: str, token: str, table_name: str, owner_tg_id: int | None):
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.message.text
        if not query:
            return

        await update.message.chat.send_action("typing")

        user = update.effective_user
        user_tg_id = user.id if user else None
        username = user.username if user else None

        try:
            chunks = await retrieve(query, table_name)
            answer = await generate(query, chunks)
        except Exception as e:
            answer = f"Sorry, an error occurred: {str(e)}"

        await update.message.reply_text(answer)

        try:
            await log_conversation(project_id, user_tg_id, username, query, answer)
        except Exception:
            pass

        if owner_tg_id and is_unanswered(answer):
            await notify_owner(token, owner_tg_id, username, query)

    return handle_message


async def _run_bot(project_id: str, token: str, table_name: str, owner_tg_id: int | None) -> None:
    """Build and run a Telegram bot with polling."""
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", _start_command))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        _make_message_handler(project_id, token, table_name, owner_tg_id),
    ))

    bot_applications[project_id] = app

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
        except Exception:
            pass
        bot_applications.pop(project_id, None)


async def start_bot(project_id: str, token: str, table_name: str, owner_tg_id: int | None = None) -> None:
    """Start a bot in a background task."""
    if project_id in running_bots and not running_bots[project_id].done():
        return

    task = asyncio.create_task(_run_bot(project_id, token, table_name, owner_tg_id))
    running_bots[project_id] = task


async def stop_bot(project_id: str) -> None:
    """Stop a running bot."""
    task = running_bots.pop(project_id, None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def is_running(project_id: str) -> bool:
    """Check if a bot is currently running."""
    task = running_bots.get(project_id)
    return task is not None and not task.done()
