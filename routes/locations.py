from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import LocationCreate
from crud import create_location
from services.auth import get_current_user
from models import Location, Device, User
from typing import List

router = APIRouter(
    prefix="/locations",
    tags=["locations"]
)


@router.post("/", response_model=LocationCreate)
async def create_location_endpoint(location: LocationCreate, db: Session = Depends(get_db),
                                   current_user: dict = Depends(get_current_user)):
    """
    Create a new location update for a device.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    device = db.query(Device).filter(Device.id == location.device_id, Device.user_id == user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db_location = create_location(db, location)

    # Update device's last known location
    device.last_location = f"POINT({location.gps_location['lon']} {location.gps_location['lat']})"
    device.last_seen = db_location.timestamp
    db.commit()

    return db_location


@router.get("/device/{device_id}", response_model=List[LocationCreate])
async def get_device_locations(device_id: int, db: Session = Depends(get_db),
                               current_user: dict = Depends(get_current_user)):
    """
    Get all location history for a specific device.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    device = db.query(Device).filter(Device.id == device_id, Device.user_id == user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    locations = db.query(Location).filter(Location.device_id == device_id).order_by(Location.timestamp.desc()).all()
    return locations


@router.get("/last/{device_id}", response_model=LocationCreate)
async def get_last_location(device_id: int, db: Session = Depends(get_db),
                            current_user: dict = Depends(get_current_user)):
    """
    Get the last known location of a specific device.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    device = db.query(Device).filter(Device.id == device_id, Device.user_id == user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    last_location = db.query(Location).filter(Location.device_id == device_id).order_by(
        Location.timestamp.desc()).first()
    if not last_location:
        raise HTTPException(status_code=404, detail="No location data found")

    return last_location