from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str
    role: str

    class Config:
        orm_mode = True