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

from core.database import SessionLocal
from core.security import verify_token
import os
from pydantic import BaseModel, ConfigDict

import hmac
import hashlib
import os
import subprocess
from typing import Dict, Any

from fastapi import (
    status, 
    BackgroundTasks
)


# GITHUB_WEBHOOK_SECRET harus diatur di file .env Anda
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET") 
if not WEBHOOK_SECRET:
    raise ValueError("GITHUB_WEBHOOK_SECRET tidak ditemukan. Setel di file .env.")


# --- MODEL PYDANTIC (FIX 422) ---

class GitHubPushEvent(BaseModel):
    # Field yang wajib Anda butuhkan
    ref: str  
    
    # Field lain yang mungkin Anda periksa
    repository: Dict[str, Any]
    sender: Dict[str, Any]
    
    # TAMBAHAN KRITIS: Memberi tahu Pydantic untuk MENGABAIKAN field JSON tambahan 
    model_config = ConfigDict(extra='ignore')

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
    allow_origins=["http://localhost:3000", "https://admin.pemudanambangan.site", "https://pemudanambangan.site"],  # Adjust in production
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

# app.py atau main.py di proyek FastAPI Anda
# --- FUNGSI KEAMANAN ---

# --- FUNGSI KEAMANAN (FIX SCOPING) ---

def verify_signature(request_body: bytes, signature: str, secret: str) -> bool:
    """Memverifikasi signature (X-Hub-Signature-256) dari GitHub."""
    if not signature:
        return False
    
    try:
        # Signature dikirim sebagai 'sha256=HEX_DIGEST'
        sha_name, signature_digest = signature.split('=')
    except ValueError:
        return False
        
    if sha_name != 'sha256':
        return False

    # Hitung HMAC dari raw request body (request_body)
    mac = hmac.new(secret.encode('utf-8'), request_body, hashlib.sha256)
    
    # Bandingkan dengan aman hasil hitungan dengan signature yang dikirim GitHub
    return hmac.compare_digest(mac.hexdigest(), signature_digest)


# --- FUNGSI DEPLOYMENT (BERJALAN DI BACKGROUND) ---

def run_deployment():
    """Menjalankan script deploy.sh."""
    
    SCRIPT_PATH = "/opt/backend-project-pemuda/deploy.sh" 
    DEPLOY_DIR = "/opt/backend-project-pemuda"
    
    # Pastikan Anda menggunakan pnpm run build:simple (atau npm install -g pnpm && pnpm install)
    # Ini sangat penting agar instalasi dependencies di server Anda sukses
    
    print(f"Deployment: Memulai script {SCRIPT_PATH}")
    
    # Jalankan deploy.sh
    subprocess.run(
        ["/bin/bash", SCRIPT_PATH], 
        check=False,
        capture_output=True, 
        text=True,
        cwd=DEPLOY_DIR,
    )
    # ... (log output sukses/gagal di sini) ...


# --- ENDPOINT UTAMA (/webhook) ---

@app.post("/webhookdeploy", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request, 
    payload: GitHubPushEvent, # Menggunakan model yang sudah di-fix (extra='ignore')
    background_tasks: BackgroundTasks
):
    # 1. Ambil raw body (raw bytes) untuk verifikasi HMAC
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    # 2. Verifikasi Secret Key
    if not verify_signature(body, signature, WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid signature: Access Denied"
        )

    # 3. Cek Event: Hanya proses 'push' ke branch 'main'
    if payload.ref == "refs/heads/main":
        print(f"Webhook Success: Push event received on {payload.ref}. Triggering deployment.")
        
        background_tasks.add_task(run_deployment)

        return {"status": "Deployment task accepted and running in background"}

    print(f"Webhook Ignored: Event on {payload.ref} skipped.")
    return {"status": "Event ignored (not a push to main)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)