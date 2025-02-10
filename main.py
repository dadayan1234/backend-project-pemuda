from fastapi import FastAPI
from database import engine, Base
from routers import auth, events, finance, attendance, schedules, news, organization, minutes
from fastapi.staticfiles import StaticFiles

app = FastAPI()

Base.metadata.create_all(bind=engine)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# Import semua router
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(finance.router)
app.include_router(attendance.router)
app.include_router(schedules.router)
app.include_router(news.router)
app.include_router(organization.router)
app.include_router(minutes.router)
