from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

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
