from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routers import projects, users
from app.database import engine, get_db, SessionLocal
from app.models import Base, Project, User
from sqlalchemy.orm import Session

app = FastAPI(title="CrowdFund Innovate")

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
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
