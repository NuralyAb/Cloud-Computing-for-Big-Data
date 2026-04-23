from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import projects, bots, auth

app = FastAPI(title="RAG Telegram Bot Builder", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(bots.router)


@app.get("/")
async def root():
    return {"message": "RAG Telegram Bot Builder API"}
