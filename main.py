# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import PyJWTError
import models
import schemas
import crud
from database import engine, get_db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="HweHweMe API",
    description="Backend API for HweHweMe AirTag Clone",
    version="1.0.0"
)

# CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 password bearer for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# Authentication Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(user_id=user_id)
    except PyJWTError:
        raise credentials_exception
    user = crud.get_user(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user


# Authentication routes
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )

    # Update last login
    crud.update_last_login(db, user)

    return {"access_token": access_token, "token_type": "bearer"}


# User Routes
@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# Device Routes
@app.post("/devices/", response_model=schemas.Device)
async def create_device(
        device: schemas.DeviceCreate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return crud.create_device(db=db, device=device, user_id=current_user.user_id)


@app.get("/devices/", response_model=List[schemas.Device])
async def read_devices(
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return crud.get_user_devices(db, user_id=current_user.user_id, skip=skip, limit=limit)


@app.get("/devices/{device_id}", response_model=schemas.Device)
async def read_device(
        device_id: str,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    device = crud.get_device(db, device_id=device_id)
    if device is None or device.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.put("/devices/{device_id}", response_model=schemas.Device)
async def update_device(
        device_id: str,
        device: schemas.DeviceUpdate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None or db_device.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Device not found")
    return crud.update_device(db=db, device_id=device_id, device=device)


@app.delete("/devices/{device_id}")
async def delete_device(
        device_id: str,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None or db_device.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Device not found")
    crud.delete_device(db=db, device_id=device_id)
    return {"detail": "Device deleted"}


# Location Routes
@app.post("/locations/", response_model=schemas.DeviceLocation)
async def create_location(
        location: schemas.DeviceLocationCreate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify if either the user owns the device or has been granted access
    device = crud.get_device(db, device_id=location.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # If user is reporting location for someone else's device
    if device.user_id != current_user.user_id:
        # Check if this device is shared publicly for location updates
        # This allows the network effect where anyone can report device locations
        shared_publicly = crud.is_device_shared_publicly(db, device_id=location.device_id)
        if not shared_publicly:
            raise HTTPException(status_code=403, detail="Not authorized to update this device's location")

    return crud.create_device_location(db=db, location=location, reported_by=location.recorded_by)


@app.get("/locations/{device_id}", response_model=List[schemas.DeviceLocation])
async def read_device_locations(
        device_id: str,
        limit: int = 10,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify ownership or access rights
    device = crud.get_device(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check ownership or shared access
    if device.user_id != current_user.user_id:
        shared_access = crud.check_device_shared_with_user(
            db, device_id=device_id, user_id=current_user.user_id
        )
        if not shared_access:
            raise HTTPException(status_code=403, detail="Not authorized to view this device's location")

    return crud.get_device_locations(db, device_id=device_id, limit=limit)


@app.get("/locations/{device_id}/latest", response_model=schemas.DeviceLocation)
async def read_device_latest_location(
        device_id: str,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify ownership or access rights
    device = crud.get_device(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check ownership or shared access
    if device.user_id != current_user.user_id:
        shared_access = crud.check_device_shared_with_user(
            db, device_id=device_id, user_id=current_user.user_id
        )
        if not shared_access:
            raise HTTPException(status_code=403, detail="Not authorized to view this device's location")

    location = crud.get_device_latest_location(db, device_id=device_id)
    if not location:
        raise HTTPException(status_code=404, detail="No location data available for this device")

    return location


# Device Group Routes
@app.post("/groups/", response_model=schemas.DeviceGroup)
async def create_group(
        group: schemas.DeviceGroupCreate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return crud.create_device_group(db=db, group=group, user_id=current_user.user_id)


@app.get("/groups/", response_model=List[schemas.DeviceGroup])
async def read_groups(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return crud.get_user_groups(db, user_id=current_user.user_id)


@app.get("/groups/{group_id}", response_model=schemas.DeviceGroup)
async def read_group(
        group_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    group = crud.get_device_group(db, group_id=group_id)
    if not group or group.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@app.put("/groups/{group_id}", response_model=schemas.DeviceGroup)
async def update_group(
        group_id: int,
        group: schemas.DeviceGroupUpdate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_group = crud.get_device_group(db, group_id=group_id)
    if not db_group or db_group.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Group not found")
    return crud.update_device_group(db=db, group_id=group_id, group=group)


@app.delete("/groups/{group_id}")
async def delete_group(
        group_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_group = crud.get_device_group(db, group_id=group_id)
    if not db_group or db_group.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Group not found")
    crud.delete_device_group(db=db, group_id=group_id)
    return {"detail": "Group deleted"}


# Group Membership Routes
@app.post("/groups/{group_id}/devices", response_model=schemas.GroupMembership)
async def add_device_to_group(
        group_id: int,
        device_id: str,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify group ownership
    group = crud.get_device_group(db, group_id=group_id)
    if not group or group.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify device ownership
    device = crud.get_device(db, device_id=device_id)
    if not device or device.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Device not found or not owned by you")

    # Add device to group
    try:
        membership = crud.add_device_to_group(db, group_id=group_id, device_id=device_id)
        return membership
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/groups/{group_id}/devices/{device_id}")
async def remove_device_from_group(
        group_id: int,
        device_id: str,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify group ownership
    group = crud.get_device_group(db, group_id=group_id)
    if not group or group.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Group not found")

    # Remove device from group
    result = crud.remove_device_from_group(db, group_id=group_id, device_id=device_id)
    if not result:
        raise HTTPException(status_code=404, detail="Device not found in group")

    return {"detail": "Device removed from group"}


# Alert Routes
@app.post("/alerts/", response_model=schemas.Alert)
async def create_alert(
        alert: schemas.AlertCreate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify device ownership or participation in the group
    device = crud.get_device(db, device_id=alert.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Simple verification - in a full implementation, you would verify 
    # that the device is either owned by the user or is in a shared group
    if device.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to create alerts for this device")

    return crud.create_alert(db=db, alert=alert)


@app.get("/alerts/", response_model=List[schemas.Alert])
async def read_alerts(
        device_id: Optional[str] = None,
        resolved: Optional[bool] = None,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return crud.get_user_alerts(
        db, user_id=current_user.user_id, device_id=device_id, resolved=resolved
    )


@app.put("/alerts/{alert_id}/resolve", response_model=schemas.Alert)
async def resolve_alert(
        alert_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    alert = crud.get_alert(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Verify ownership of the device or alert
    device = crud.get_device(db, device_id=alert.device_id)
    if not device or device.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to resolve this alert")

    return crud.resolve_alert(db=db, alert_id=alert_id)


# Device Sharing Routes
@app.post("/shares/", response_model=schemas.SharedDevice)
async def share_device(
        share: schemas.SharedDeviceCreate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify device ownership
    device = crud.get_device(db, device_id=share.device_id)
    if not device or device.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Device not found or not owned by you")

    # Verify target user exists
    target_user = crud.get_user_by_email(db, email=share.shared_with_email)
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    # Create sharing
    return crud.share_device(
        db=db,
        device_id=share.device_id,
        owner_id=current_user.user_id,
        shared_with_id=target_user.user_id,
        permission_level=share.permission_level,
        expires_at=share.expires_at
    )


@app.get("/shares/", response_model=List[schemas.SharedDevice])
async def read_shared_devices(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Get devices shared by the user
    return crud.get_devices_shared_by_user(db, user_id=current_user.user_id)


@app.get("/shares/with-me", response_model=List[schemas.SharedDevice])
async def read_devices_shared_with_me(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Get devices shared with the user
    return crud.get_devices_shared_with_user(db, user_id=current_user.user_id)


@app.delete("/shares/{share_id}")
async def remove_device_sharing(
        share_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Verify share ownership
    share = crud.get_device_share(db, share_id=share_id)
    if not share or share.owner_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Share not found or not owned by you")

    # Remove sharing
    crud.delete_device_share(db=db, share_id=share_id)
    return {"detail": "Device sharing removed"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8085)