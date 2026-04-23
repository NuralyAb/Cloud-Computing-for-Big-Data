from services.supabase_service import supabase


def is_unanswered(answer: str) -> bool:
    """Detect if the bot's answer indicates it has no relevant knowledge."""
    if not answer:
        return True
    markers = [
        "i don't have information",
        "don't have information",
        "i don't know",
        "не могу ответить",
        "нет информации",
        "не располагаю",
    ]
    lower = answer.lower()
    return any(m in lower for m in markers)


async def log_conversation(
    project_id: str,
    user_tg_id: int | None,
    username: str | None,
    question: str,
    answer: str,
) -> None:
    """Save a user-bot interaction to the database."""
    supabase.table("conversations").insert({
        "project_id": project_id,
        "user_tg_id": user_tg_id,
        "username": username,
        "question": question,
        "answer": answer,
        "answered": not is_unanswered(answer),
    }).execute()


async def get_analytics(project_id: str) -> dict:
    """Aggregate analytics for a project's conversations."""
    total = supabase.table("conversations").select("id", count="exact").eq("project_id", project_id).execute()
    answered = supabase.table("conversations").select("id", count="exact").eq("project_id", project_id).eq("answered", True).execute()
    unanswered = supabase.table("conversations").select("id", count="exact").eq("project_id", project_id).eq("answered", False).execute()

    # Unique users
    users_result = supabase.table("conversations").select("user_tg_id").eq("project_id", project_id).execute()
    unique_users = len({r["user_tg_id"] for r in (users_result.data or []) if r.get("user_tg_id")})

    # Activity by day (last 14 days)
    activity_sql = f"""
    SELECT to_char(created_at, 'YYYY-MM-DD') AS day, count(*) AS cnt
    FROM conversations
    WHERE project_id = '{project_id}'
      AND created_at >= now() - interval '14 days'
    GROUP BY day
    ORDER BY day
    """
    activity_res = supabase.rpc("exec_sql", {"query": activity_sql}).execute()
    activity = activity_res.data if activity_res.data else []

    # Top 10 questions (grouped by similar text — simple exact match, lowercased, trimmed)
    top_sql = f"""
    SELECT trim(lower(question)) AS q, count(*) AS cnt
    FROM conversations
    WHERE project_id = '{project_id}'
    GROUP BY q
    ORDER BY cnt DESC
    LIMIT 10
    """
    top_res = supabase.rpc("exec_sql", {"query": top_sql}).execute()
    top_questions = top_res.data if top_res.data else []

    return {
        "total_messages": total.count or 0,
        "answered": answered.count or 0,
        "unanswered": unanswered.count or 0,
        "unique_users": unique_users,
        "activity": activity,
        "top_questions": top_questions,
    }


async def get_unanswered_questions(project_id: str) -> list[dict]:
    """Return grouped unanswered questions with counts and last occurrence."""
    sql = f"""
    SELECT
        trim(lower(question)) AS question,
        count(*) AS count,
        max(created_at) AS last_asked
    FROM conversations
    WHERE project_id = '{project_id}' AND answered = false
    GROUP BY trim(lower(question))
    ORDER BY count DESC, last_asked DESC
    LIMIT 50
    """
    result = supabase.rpc("exec_sql", {"query": sql}).execute()
    return result.data if result.data else []
