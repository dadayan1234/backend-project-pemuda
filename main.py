from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import (
    auth, events, finance, member,
    news, minutes, #schedules,
    uploads, notification
)
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
import os

app = FastAPI(
    title="Business Process API",
    description="API for organization management",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Authentication"},
        {"name": "events", "description": "Event management"},
        {"name": "finances", "description": "Financial management"},
        {"name": "members", "description": "Member management"},
        {"name": "news", "description": "News management"},
        {"name": "schedules", "description": "Schedule management"},
        {"name": "meeting-minutes", "description": "Meeting minutes management"},
        {"name": "uploads", "description": "File upload management"},
        {"name": "notifications", "description": "Notification management"}
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://opnweb.vercel.app", "https://opnadmin.netlify.app"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Ensure the uploads directory exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")



# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["finances"])
app.include_router(member.router, prefix="/api/v1/members", tags=["members"])
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])
# app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])
app.include_router(minutes.router, prefix="/api/v1/meeting-minutes", tags=["meeting-minutes"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["uploads"])
app.include_router(notification.router, prefix="/api/v1/notifications", tags=["notifications"])

security = HTTPBasic()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)