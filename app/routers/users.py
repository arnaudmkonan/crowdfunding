from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth, email
from pydantic import EmailStr

router = APIRouter()

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password, is_verified=True)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"User created: {db_user.id}, {db_user.username}, {db_user.email}")  # Add this line for debugging
    return db_user

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = email.verify_email_token(token)
        user_email = payload["email"]
        db_user = db.query(models.User).filter(models.User.email == user_email).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        if db_user.is_verified:
            return {"message": "Email already verified"}
        db_user.is_verified = True
        db.commit()
        return {"message": "Email verified successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")

@router.get("/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
