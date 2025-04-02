from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Device
from schemas import DeviceCreate, DeviceResponse
from crud import create_device
from services.auth import get_current_user

router = APIRouter()

@router.post("/devices", response_model=DeviceResponse)
async def create_new_device(device: DeviceCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return create_device(db, device, user.id)