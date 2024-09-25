from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth

router = APIRouter()

@router.post("/", response_model=schemas.Investment, status_code=status.HTTP_201_CREATED)
def create_investment(investment: schemas.InvestmentCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role != schemas.UserRole.INVESTOR:
        raise HTTPException(status_code=403, detail="Only investors can make investments")
    db_investment = models.Investment(**investment.dict(), investor_id=current_user.id)
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment

@router.get("/", response_model=list[schemas.Investment])
def read_investments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    investments = db.query(models.Investment).filter(models.Investment.investor_id == current_user.id).offset(skip).limit(limit).all()
    return investments

@router.get("/{investment_id}", response_model=schemas.Investment)
def read_investment(investment_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_investment = db.query(models.Investment).filter(models.Investment.id == investment_id, models.Investment.investor_id == current_user.id).first()
    if db_investment is None:
        raise HTTPException(status_code=404, detail="Investment not found")
    return db_investment

@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(investment_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_investment = db.query(models.Investment).filter(models.Investment.id == investment_id, models.Investment.investor_id == current_user.id).first()
    if db_investment is None:
        raise HTTPException(status_code=404, detail="Investment not found")
    db.delete(db_investment)
    db.commit()
    return {"message": "Investment deleted successfully"}
