from sqlalchemy.orm import Session
from models import User, Device, Group, GroupDevice, Location
from schemas import UserCreate, DeviceCreate, GroupCreate, LocationCreate
from services.auth import get_password_hash

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_device(db: Session, device: DeviceCreate, user_id: int):
    db_device = Device(user_id=user_id, name=device.name, ble_id=device.ble_id, last_location=f"POINT({device.last_location['lon']} {device.last_location['lat']})")
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

def create_group(db: Session, group: GroupCreate, user_id: int):
    db_group = Group(user_id=user_id, name=group.name)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def add_device_to_group(db: Session, group_id: int, device_id: int):
    db_group_device = GroupDevice(group_id=group_id, device_id=device_id)
    db.add(db_group_device)
    db.commit()
    return db_group_device

def create_location(db: Session, location: LocationCreate):
    db_location = Location(device_id=location.device_id, gps_location=f"POINT({location.gps_location['lon']} {location.gps_location['lat']})", signal_strength=location.signal_strength)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


def verify_password():
    return None