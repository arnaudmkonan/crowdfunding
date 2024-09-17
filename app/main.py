from fastapi import FastAPI
from app.routers import projects, users
from app.database import engine
from app.models import Base

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(projects.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Crowdfunding Platform API"}
