from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    INVESTOR = "investor"
    ENTREPRENEUR = "entrepreneur"
    ADMIN = "admin"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.INVESTOR

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    is_verified: bool = False
    created_at: datetime

    class Config:
        orm_mode = True

class User(UserInDB):
    pass

class CompanyBase(BaseModel):
    name: str
    description: str

class CompanyCreate(CompanyBase):
    owner_id: int

class CompanyInDB(CompanyBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Company(CompanyInDB):
    owner: User

class CampaignBase(BaseModel):
    title: str
    description: str
    goal_amount: float
    end_date: datetime

class CampaignCreate(CampaignBase):
    company_id: int

class CampaignInDB(CampaignBase):
    id: int
    current_amount: float
    company_id: int
    start_date: datetime
    status: str

    class Config:
        orm_mode = True

class Campaign(CampaignInDB):
    company: Company

class InvestmentBase(BaseModel):
    amount: float

class InvestmentCreate(InvestmentBase):
    investor_id: int
    campaign_id: int

class InvestmentInDB(InvestmentBase):
    id: int
    investor_id: int
    campaign_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Investment(InvestmentInDB):
    investor: User
    campaign: Campaign

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenResponse(Token):
    refresh_token: str

class TokenData(BaseModel):
    username: Optional[str] = None
