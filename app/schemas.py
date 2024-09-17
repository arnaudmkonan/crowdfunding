from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    projects: list["Project"] = []

    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    title: str
    description: str
    goal_amount: float

class ProjectCreate(ProjectBase):
    creator_id: int

class Project(ProjectBase):
    id: int
    current_amount: float
    created_at: datetime
    creator: User

    class Config:
        orm_mode = True

User.update_forward_refs()
