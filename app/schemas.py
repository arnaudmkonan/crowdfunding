from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, ForwardRef

User = ForwardRef('User')

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

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
    creator_id: int
    creator: Optional[User] = None

    class Config:
        orm_mode = True

Project.update_forward_refs()

class User(UserBase):
    id: int
    projects: List[Project] = []

    class Config:
        orm_mode = True
