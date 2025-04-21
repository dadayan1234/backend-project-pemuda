from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.v1.endpoints import (
    auth, events, finance, member,
    news, minutes, feedback,
    uploads, notification, file
)
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
import os

from core.database import SessionLocal
from core.security import verify_token

app = FastAPI(
    title="OPN API",
    description="API for organization management",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Authentication"},
        {"name": "events", "description": "Event management"},
        {"name": "finances", "description": "Financial management"},
        {"name": "members", "description": "Member management"},
        {"name": "news", "description": "News management"},
        {"name": "feedback", "description": "Feedback management"},
        {"name": "meeting-minutes", "description": "Meeting minutes management"},
        {"name": "Uploads - News", "description": "Upload files related to news"},
        {"name": "Uploads - Events", "description": "Upload files related to events"},
        {"name": "Uploads - Finance", "description": "Upload finance documents"},
        {"name": "Uploads - User", "description": "Upload user profile photos"},
        {"name": "notifications", "description": "Notification management"}
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://opnweb-virid.vercel.app/"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Ensure the uploads directory exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

security = HTTPBasic()
# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["finances"])
app.include_router(member.router, prefix="/api/v1/members", tags=["members"])
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(minutes.router, prefix="/api/v1/meeting-minutes", tags=["meeting-minutes"])
app.include_router(uploads.router, prefix="/api/v1/uploads")
app.include_router(notification.router, prefix="/api/v1/notifications", tags=["notifications"])
# Di main.py, sebelum app.mount

# Ganti app.mount dengan ini:
app.include_router(file.router, tags=["file"])

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path.lstrip('/')
    if path.startswith("/uploads/"):
        # Biarkan router FastAPI yang handle
        return await call_next(request)

    return await call_next(request)
# @app.middleware("http")
# async def auth_middleware(request: Request, call_next):
#     # Biarkan request ke endpoint API langsung pass
#     if request.url.path.startswith('/api/'):
#         return await call_next(request)

#     # Tangani request ke /uploads/
#     if request.url.path.startswith('/uploads/'):
#         try:
#             from api.v1.endpoints.file import protected_file
#             file_path = request.url.path[len('/uploads/'):]
            
#             # Buat request baru dengan path yang sudah dinormalisasi
#             modified_request = request
#             modified_request.scope["path"] = f"/{file_path}"
            
#             return await protected_file(modified_request, file_path)
#         except HTTPException as e:
#             from fastapi.responses import JSONResponse
#             return JSONResponse(
#                 status_code=e.status_code,
#                 content={"detail": e.detail}
#             )

#     return await call_next(request)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)