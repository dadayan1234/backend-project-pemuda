from fastapi import FastAPI
from api.v1.endpoints import auth, events, finances, members, news, schedules, meeting_minutes, uploads

app = FastAPI()

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(finances.router, prefix="/api/v1/finances", tags=["finances"])
app.include_router(members.router, prefix="/api/v1/members", tags=["members"])
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])
app.include_router(meeting_minutes.router, prefix="/api/v1/meeting-minutes", tags=["meeting-minutes"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["uploads"])