from fastapi import FastAPI, Request, Depends, HTTPException, status, BackgroundTasks, Response, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import timedelta, datetime
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from app.schemas import UserRole
from typing import Optional

from app import auth, schemas, email as email_module
from app.auth import SECRET_KEY, ALGORITHM
from app.routers import campaigns, users, companies, investments
from app import models, schemas, auth
from app.database import engine

import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add a rotating file handler
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Add a stream handler for console output
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

logger.info("Application starting...")
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
    token = email_module.create_email_verification_token(user.email)
    background_tasks.add_task(email_module.send_email_verification, user.email, token)
    logger.info(f"Verification email task added for user: {user.email}")
    
    return db_user

# Add this new route for user login
@app.post("/token")
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

@app.post("/login", response_class=HTMLResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    token_data = await login_for_access_token(form_data, db)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {token_data['access_token']}", 
        httponly=True, 
        max_age=1800,
        expires=1800,
        samesite="Lax",
        secure=False  # set to True if using HTTPS
    )
    return response

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
    current_user = await get_current_user_or_none(request, db)
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects, "current_user": current_user})

@app.get("/campaigns")
async def campaigns(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Campaign).all()
    current_user = await get_current_user_or_none(request, db)
    return templates.TemplateResponse("campaigns.html", {"request": request, "projects": projects, "current_user": current_user})

@app.get("/campaign/{campaign_id}")
async def campaign_detail(request: Request, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    current_user = await get_current_user_or_none(request, db)
    return templates.TemplateResponse("campaign_detail.html", {"request": request, "campaign": campaign, "current_user": current_user})

@app.get("/how-it-works")
async def how_it_works(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_or_none(request, db)
    return templates.TemplateResponse("how_it_works.html", {"request": request, "current_user": current_user})

@app.get("/signup")
async def signup(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_or_none(request, db)
    return templates.TemplateResponse("sign_up.html", {"request": request, "current_user": current_user})

@app.get("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_or_none(request, db)
    return templates.TemplateResponse("login.html", {"request": request, "current_user": current_user})

@app.get("/reset-password")
async def reset_password(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user_or_none(request, db)
    return templates.TemplateResponse("reset_password.html", {"request": request, "current_user": current_user})

async def get_current_user_or_none(request: Request, db: Session):
    try:
        return await auth.get_current_user(request, db)
    except HTTPException:
        return None

@app.post("/reset-password")
async def reset_password_request(request: Request, background_tasks: BackgroundTasks = BackgroundTasks(), db: Session = Depends(get_db)):
    form_data = await request.form()
    email_address = form_data.get("email")
    if email_address:
        user = db.query(models.User).filter(models.User.email == email_address).first()
        if user:
            token = auth.create_password_reset_token(email_address)
            background_tasks.add_task(email_module.send_password_reset_email, email_address, token)
    return {"message": "If an account with that email exists, a password reset link has been sent."}

@app.get("/reset-password/{token}")
async def reset_password_form(request: Request, token: str):
    return templates.TemplateResponse("reset_password_form.html", {"request": request, "token": token})

@app.post("/reset-password/{token}")
async def reset_password_submit(token: str, new_password: str = Form(...), db: Session = Depends(get_db)):
    email = auth.verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

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
    progress_percentage = (campaign.current_amount / campaign.goal_amount) * 100 if campaign.goal_amount > 0 else 0
    
    return templates.TemplateResponse("campaign_detail.html", {
        "request": request, 
        "campaign": campaign,
        "company": company,
        "progress_percentage": progress_percentage
    })

@app.post("/api/kyc")
async def update_kyc(
    request: Request,
    full_name: str = Form(...),
    date_of_birth: str = Form(...),
    address: str = Form(...),
    id_number: str = Form(...),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    # Update user's KYC information
    current_user.full_name = full_name
    current_user.date_of_birth = date_of_birth
    current_user.address = address
    current_user.id_number = id_number
    current_user.kyc_verified = True
    db.commit()
    return {"message": "KYC information updated successfully"}

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
@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = await auth.get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    context = {
        "request": request,
        "current_user": current_user,
    }
    
    if current_user.role == schemas.UserRole.INVESTOR:
        investments = db.query(models.Investment).filter(models.Investment.investor_id == current_user.id).all()
        total_invested = sum(investment.amount for investment in investments)
        num_investments = len(investments)
        
        # Calculate total returns and ROI (this is a placeholder, you should implement the actual logic)
        total_returns = total_invested * 1.1  # Assuming 10% return for demonstration
        roi = ((total_returns - total_invested) / total_invested) * 100 if total_invested > 0 else 0
        
        # Add current value and ROI to each investment (placeholder logic)
        for investment in investments:
            investment.current_value = investment.amount * 1.1
            investment.roi = ((investment.current_value - investment.amount) / investment.amount) * 100
        
        # Fetch recent transactions (placeholder data)
        transactions = [
            {"date": datetime.now() - timedelta(days=i), "type": "Investment", "amount": 1000, "campaign_title": f"Campaign {i}", "status": "completed"}
            for i in range(5)
        ]
        
        context.update({
            "investments": investments,
            "total_invested": total_invested,
            "num_investments": num_investments,
            "total_returns": total_returns,
            "roi": roi,
            "transactions": transactions
        })
    elif current_user.role == schemas.UserRole.ENTREPRENEUR:
        campaigns = db.query(models.Campaign).filter(models.Campaign.company_id == current_user.company.id).all()
        total_raised = sum(campaign.current_amount for campaign in campaigns)
        num_campaigns = len(campaigns)
        
        context.update({
            "campaigns": campaigns,
            "total_raised": total_raised,
            "num_campaigns": num_campaigns
        })
    
    return templates.TemplateResponse("dashboard.html", context)

@app.post("/api/update-profile")
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    date_of_birth: str = Form(...),
    address: str = Form(...),
    id_number: str = Form(...),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    current_user.full_name = full_name
    current_user.date_of_birth = date_of_birth
    current_user.address = address
    current_user.id_number = id_number
    db.commit()
    return {"message": "Profile updated successfully"}

@app.post("/api/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    if not auth.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    current_user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@app.post("/api/upload-kyc-documents")
async def upload_kyc_documents(
    request: Request,
    id_proof: UploadFile = File(...),
    address_proof: UploadFile = File(...),
    business_proof: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    # Save the uploaded files
    id_proof_path = f"kyc_documents/{current_user.id}_id_proof.pdf"
    address_proof_path = f"kyc_documents/{current_user.id}_address_proof.pdf"
    
    with open(id_proof_path, "wb") as buffer:
        buffer.write(await id_proof.read())
    with open(address_proof_path, "wb") as buffer:
        buffer.write(await address_proof.read())
    
    if current_user.role == schemas.UserRole.ENTREPRENEUR and business_proof:
        business_proof_path = f"kyc_documents/{current_user.id}_business_proof.pdf"
        with open(business_proof_path, "wb") as buffer:
            buffer.write(await business_proof.read())
    
    # Update user's KYC status
    current_user.kyc_status = "submitted"
    db.commit()
    
    return {"message": "KYC documents uploaded successfully"}
