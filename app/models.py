from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from app.schemas import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.INVESTOR)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # KYC information
    full_name = Column(String)
    date_of_birth = Column(String)
    address = Column(String)
    id_number = Column(String)
    kyc_verified = Column(Boolean, default=False)
    
    # Relationships
    company = relationship("Company", back_populates="owner", uselist=False)
    investments = relationship("Investment", back_populates="investor")

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="company")
    campaigns = relationship("Campaign", back_populates="company")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    goal_amount = Column(Float)
    current_amount = Column(Float, default=0)
    company_id = Column(Integer, ForeignKey("companies.id"))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    status = Column(String, default="active")  # active, completed, cancelled

    # Relationships
    company = relationship("Company", back_populates="campaigns")
    investments = relationship("Investment", back_populates="campaign")

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    investor_id = Column(Integer, ForeignKey("users.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    investor = relationship("User", back_populates="investments")
    campaign = relationship("Campaign", back_populates="investments")
