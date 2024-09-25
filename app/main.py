from fastapi import FastAPI, Request, Depends, HTTPException, status, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

from app import auth, schemas, email
from app.routers import projects, users
from app import models, schemas, auth
from app.database import engine

models.Base.metadata.create_all(bind=engine)
from app.database import engine, get_db, SessionLocal
from app.models import Base, Project, User
from sqlalchemy.orm import Session

app = FastAPI(title="CrowdFund Innovate")

# Add this new route for user registration
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/api/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logger.info(f"Attempting to create user with email: {user.email}")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        logger.warning(f"User with email {user.email} already exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password, is_verified=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created successfully with id: {db_user.id}")
    
    # Generate and send verification email
    token = email.create_email_verification_token(user.email)
    background_tasks.add_task(email.send_email_verification, user.email, token)
    logger.info(f"Verification email task added for user: {user.email}")
    
    return db_user

# Create database tables
Base.metadata.create_all(bind=engine)

def add_sample_data(db: Session):
    # Check if there are any projects in the database
    if db.query(Project).count() == 0:
        # Create a sample user
        sample_user = User(username="sample_user", email="sample@example.com", hashed_password="hashed_password")
        db.add(sample_user)
        db.commit()
        db.refresh(sample_user)

        # Create sample projects
        sample_projects = [
            Project(
                title="EcoTech Solutions",
                description="Revolutionizing renewable energy with cutting-edge solar technology.",
                goal_amount=1000000,
                current_amount=750000,
                creator_id=sample_user.id
            ),
            Project(
                title="UrbanFarm",
                description="Transforming urban spaces into sustainable vertical farms for local food production.",
                goal_amount=500000,
                current_amount=300000,
                creator_id=sample_user.id
            ),
            Project(
                title="AI Education Platform",
                description="Personalized learning experiences powered by artificial intelligence.",
                goal_amount=750000,
                current_amount=400000,
                creator_id=sample_user.id
            ),
            Project(
                title="HealthAI",
                description="Using AI to revolutionize personalized healthcare and early disease detection.",
                goal_amount=1000000,
                current_amount=600000,
                creator_id=sample_user.id
            )
        ]
        db.add_all(sample_projects)
        db.commit()

# Add sample data
with SessionLocal() as db:
    add_sample_data(db)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects})

@app.get("/campaigns")
async def campaigns(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return templates.TemplateResponse("campaigns.html", {"request": request, "projects": projects})

@app.get("/startups")
async def startups(request: Request):
    return RedirectResponse(url="/campaigns")

@app.get("/startup/{startup_id}")
async def startup_detail(request: Request, startup_id: str):
    # In a real application, you would fetch the startup details from the database
    # For now, we'll use a dummy startup
    startup = {
        "id": startup_id,
        "name": "HealthAI",
        "tagline": "Personalized healthcare through advanced machine learning algorithms",
        "description": "HealthAI is revolutionizing the healthcare industry by leveraging cutting-edge artificial intelligence and machine learning technologies to provide personalized healthcare solutions.",
        "raised": 200000,
        "goal": 500000,
    }
    return templates.TemplateResponse("startup_detail.html", {"request": request, "startup": startup})

@app.get("/signup")
async def signup(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})

@app.get("/verify-email")
async def verify_email(request: Request, token: str, db: Session = Depends(get_db)):
    try:
        payload = email.verify_email_token(token)
        user_email = payload["email"]
        db_user = db.query(models.User).filter(models.User.email == user_email).first()
        if not db_user:
            logger.warning(f"User not found for email: {user_email}")
            return templates.TemplateResponse("email_verification.html", {"request": request, "message": "User not found", "status": "error"})
        if db_user.is_verified:
            logger.info(f"Email already verified for user: {user_email}")
            return templates.TemplateResponse("email_verification.html", {"request": request, "message": "Email already verified", "status": "info"})
        db_user.is_verified = True
        db.commit()
        logger.info(f"Email verified successfully for user: {user_email}")
        return templates.TemplateResponse("email_verification.html", {"request": request, "message": "Email verified successfully", "status": "success"})
    except ValueError as e:
        logger.error(f"Invalid token: {str(e)}")
        return templates.TemplateResponse("email_verification.html", {"request": request, "message": "Invalid or expired token", "status": "error"})
    except Exception as e:
        logger.error(f"Error during email verification: {str(e)}")
        return templates.TemplateResponse("email_verification.html", {"request": request, "message": "An error occurred during verification", "status": "error"})

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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/dashboard")
async def dashboard(request: Request, current_user: schemas.User = Depends(auth.get_current_active_user)):
    try:
        # Here you would fetch the user's investments and other relevant data
        # For now, we'll use dummy data
        investments = [
            {"project_id": 1, "project_name": "EcoTech Solutions", "amount": 5000, "date": "2023-05-01", "status": "Active"},
            {"project_id": 2, "project_name": "UrbanFarm", "amount": 3000, "date": "2023-04-15", "status": "Active"},
        ]
        total_invested = sum(inv["amount"] for inv in investments)
        num_investments = len(investments)
        
        print(f"Dashboard accessed by user: {current_user.id}, {current_user.username}")  # Add this line for debugging
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "current_user": current_user,
            "investments": investments,
            "total_invested": total_invested,
            "num_investments": num_investments
        })
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")  # Add this line for debugging
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api")
async def api_root(request: Request):
    api_info = {
        "version": "1.0.0",
        "title": "CrowdFund Innovate API",
        "description": "API for managing crowdfunding campaigns and user interactions",
        "base_url": "/api",
        "endpoints": [
            {
                "path": "/users",
                "methods": ["GET", "POST"],
                "description": "Manage user accounts"
            },
            {
                "path": "/projects",
                "methods": ["GET", "POST"],
                "description": "Manage crowdfunding projects"
            },
            {
                "path": "/projects/{project_id}",
                "methods": ["GET", "PUT", "DELETE"],
                "description": "Manage individual project details"
            },
            {
                "path": "/projects/{project_id}/fund",
                "methods": ["PUT"],
                "description": "Fund a specific project"
            }
        ]
    }
    return templates.TemplateResponse("api.html", {"request": request, "api_info": api_info})


# Add these new endpoints
@app.post("/token", response_model=schemas.TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    refresh_token = auth.create_refresh_token(data={"sub": user.username})
    print(f"User authenticated: {user.id}, {user.username}")  # Add this line for debugging
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/token/refresh", response_model=schemas.TokenResponse)
async def refresh_token(refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        access_token = auth.create_access_token(data={"sub": user.username})
        new_refresh_token = auth.create_refresh_token(data={"sub": user.username})
        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return current_user

@app.get("/dashboard")
async def dashboard(request: Request, current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    try:
        # Fetch user's investments
        investments = db.query(models.Project).filter(models.Project.creator_id == current_user.id).all()
        
        # Calculate total invested and number of investments
        total_invested = sum(inv.current_amount for inv in investments)
        num_investments = len(investments)
        
        print(f"Dashboard accessed by user: {current_user.id}, {current_user.username}")
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "current_user": current_user,
            "investments": investments,
            "total_invested": total_invested,
            "num_investments": num_investments
        })
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
