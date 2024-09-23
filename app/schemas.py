from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

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

class ProjectInDB(ProjectBase):
    id: int
    current_amount: float
    created_at: datetime
    creator_id: int

    class Config:
        orm_mode = True

class UserInDB(UserBase):
    id: int
    is_verified: bool = False

    class Config:
        orm_mode = True

class Project(ProjectInDB):
    creator: Optional[UserInDB] = None

class User(UserInDB):
    projects: List[ProjectInDB] = []
# Add these new schemas at the end of the file

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenResponse(Token):
    refresh_token: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserInDB(User):
    hashed_password: str
