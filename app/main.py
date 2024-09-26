from fastapi import FastAPI, Request, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from datetime import timedelta, datetime
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from app.schemas import UserRole

from app import auth, schemas, email
from app.routers import campaigns, users, companies, investments
from app import models, schemas, auth
from app.database import engine

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Creating database tables...")
models.Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

from app.database import engine, get_db, SessionLocal
from app.models import Base, Campaign, User, Company, Investment
from sqlalchemy.orm import Session

app = FastAPI(title="CrowdFund Innovate")

# Add this new route for user registration
@app.post("/api/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logger.info(f"Attempting to create user with email: {user.email}")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        logger.warning(f"User with email {user.email} already exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password, is_verified=False, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created successfully with id: {db_user.id}")
    
    # Generate and send verification email
    token = email.create_email_verification_token(user.email)
    background_tasks.add_task(email.send_email_verification, user.email, token)
    logger.info(f"Verification email task added for user: {user.email}")
    
    return db_user

# Add this new route for user login
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Create database tables
Base.metadata.create_all(bind=engine)

def add_sample_data(db: Session):
    logger.info("Checking if sample data needs to be added...")
    # Check if there are any campaigns in the database
    if db.query(Campaign).count() == 0:
        logger.info("No existing campaigns found. Adding sample data...")
        # Create sample users
        sample_user1 = User(
            username="sample_user",
            email="sample@example.com",
            hashed_password="hashed_password",
            role=UserRole.ENTREPRENEUR,  # Use UserRole enum directly
            is_verified=True
        )
        sample_user2 = User(
            username="test_user",
            email="test@example.com",
            hashed_password="hashed_password",
            role=UserRole.INVESTOR,  # Use UserRole enum directly
            is_verified=True
        )
        db.add(sample_user1)
        db.add(sample_user2)
        db.commit()
        db.refresh(sample_user1)
        db.refresh(sample_user2)
        logger.info(f"Sample users created: {sample_user1.id}, {sample_user2.id}")

        # Create sample companies
        sample_company1 = Company(
            name="EcoTech Solutions",
            description="Revolutionizing renewable energy",
            owner_id=sample_user1.id
        )
        sample_company2 = Company(
            name="UrbanFarm",
            description="Transforming urban spaces into sustainable farms",
            owner_id=sample_user1.id
        )
        db.add(sample_company1)
        db.add(sample_company2)
        db.commit()
        db.refresh(sample_company1)
        db.refresh(sample_company2)
        logger.info(f"Sample companies created: {sample_company1.id}, {sample_company2.id}")

        # Create sample campaigns
        sample_campaigns = [
            Campaign(
                title="Solar Power Revolution",
                description="Cutting-edge solar technology for sustainable energy.",
                goal_amount=1000000,
                current_amount=750000,
                company_id=sample_company1.id,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
                status="active"
            ),
            Campaign(
                title="Vertical Farming Initiative",
                description="Transforming urban spaces into productive farms.",
                goal_amount=500000,
                current_amount=300000,
                company_id=sample_company2.id,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=60),
                status="active"
            )
        ]
        db.add_all(sample_campaigns)
        db.commit()
        for campaign in sample_campaigns:
            db.refresh(campaign)
        logger.info(f"Sample campaigns created: {len(sample_campaigns)}")

        # Create sample investments
        sample_investments = [
            Investment(
                amount=50000,
                investor_id=sample_user2.id,
                campaign_id=sample_campaigns[0].id
            ),
            Investment(
                amount=30000,
                investor_id=sample_user2.id,
                campaign_id=sample_campaigns[1].id
            )
        ]
        db.add_all(sample_investments)
        db.commit()
        logger.info(f"Sample investments created: {len(sample_investments)}")
    else:
        logger.info("Sample data already exists. Skipping sample data creation.")

# Add sample data
logger.info("Initializing database session to add sample data...")
with SessionLocal() as db:
    add_sample_data(db)
logger.info("Sample data addition process completed.")

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(investments.router, prefix="/api/investments", tags=["investments"])

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Campaign).all()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects})

@app.get("/campaigns")
async def campaigns(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Campaign).all()
    return templates.TemplateResponse("campaigns.html", {"request": request, "projects": projects})

@app.get("/campaign/{campaign_id}")
async def campaign_detail(request: Request, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return templates.TemplateResponse("campaign_detail.html", {"request": request, "campaign": campaign})

@app.get("/how-it-works")
async def how_it_works(request: Request):
    return templates.TemplateResponse("how_it_works.html", {"request": request})

@app.get("/signup")
async def signup(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})

@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/campaign/{campaign_id}")
async def campaign_detail(request: Request, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Fetch the associated company
    company = db.query(models.Company).filter(models.Company.id == campaign.company_id).first()
    
    # Calculate progress percentage
    progress_percentage = (campaign.current_amount / campaign.goal_amount) * 100
    
    return templates.TemplateResponse("campaign_detail.html", {
        "request": request, 
        "campaign": campaign,
        "company": company,
        "progress_percentage": progress_percentage
    })

@app.post("/invest/{campaign_id}")
async def invest_in_campaign(
    request: Request, 
    campaign_id: int, 
    investment_amount: float = Form(...), 
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Create a new investment
    new_investment = models.Investment(
        amount=investment_amount,
        investor_id=current_user.id,
        campaign_id=campaign_id
    )
    db.add(new_investment)

    # Update campaign's current amount
    campaign.current_amount += investment_amount
    db.add(campaign)
    
    db.commit()
    db.refresh(campaign)
    db.refresh(new_investment)

    return RedirectResponse(url=f"/campaign/{campaign_id}", status_code=303)

# ... (keep the rest of the routes as they are)
