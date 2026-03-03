from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, chat, goals, onboarding, profile, reports, transactions

app = FastAPI(
    title="Finance Advisor API",
    description="Personal finance advisor with AI-powered analysis",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(onboarding.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(goals.router)
app.include_router(chat.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
