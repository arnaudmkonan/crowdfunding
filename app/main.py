from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.routers import projects, users
from app.database import engine, get_db
from app.models import Base, Project
from sqlalchemy.orm import Session

app = FastAPI(title="CrowdFund Innovate")

# Create database tables
Base.metadata.create_all(bind=engine)

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
async def api_root():
    return {"message": "Welcome to the CrowdFund Innovate API"}
