# crud.py
from sqlalchemy.orm import Session
from models import User, Device, DeviceLocation, DeviceGroup, GroupMembership, Alert, SharedDevice, Location
from schemas import UserCreate, DeviceCreate, DeviceUpdate, DeviceLocationCreate, DeviceGroupCreate, DeviceGroupUpdate, \
    GroupMembershipCreate, AlertCreate, SharedDeviceCreate, LocationCreate
from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, full_name=user.full_name, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_device(db: Session, device: DeviceCreate, user_id: int):
    db_device = Device(**device.dict(), user_id=user_id)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

def update_device(db: Session, device_id: str, device_update: DeviceUpdate):
    db_device = db.query(Device).filter(Device.device_id == device_id).first()
    if db_device:
        for key, value in device_update.dict(exclude_unset=True).items():
            setattr(db_device, key, value)
        db.commit()
        db.refresh(db_device)
    return db_device

def create_device_location(db: Session, location: DeviceLocationCreate):
    db_location = DeviceLocation(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def create_device_group(db: Session, group: DeviceGroupCreate, user_id: int):
    db_group = DeviceGroup(**group.dict(), user_id=user_id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def add_device_to_group(db: Session, membership: GroupMembershipCreate):
    db_membership = GroupMembership(**membership.dict())
    db.add(db_membership)
    db.commit()
    db.refresh(db_membership)
    return db_membership

def create_alert(db: Session, alert: AlertCreate):
    db_alert = Alert(**alert.dict(), created_at=datetime.utcnow())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def create_shared_device(db: Session, shared_device: SharedDeviceCreate, owner_id: int, shared_with_id: int):
    db_shared = SharedDevice(**shared_device.dict(), owner_id=owner_id, shared_with_id=shared_with_id)
    db.add(db_shared)
    db.commit()
    db.refresh(db_shared)
    return db_shared


def get_device(db: Session, device_id: str):
    return db.query(Device).filter(Device.id == device_id).first()

def get_devices_by_owner(db: Session, owner_id: int):
    return db.query(Device).filter(Device.owner_id == owner_id).all()

def create_location(db: Session, location: LocationCreate, device_id: int):
    db_location = Location(**location.dict(), device_id=device_id, timestamp=datetime.utcnow())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_latest_location(db: Session, device_id: int):
    return db.query(Location).filter(Location.device_id == device_id).order_by(Location.timestamp.desc()).first()


def get_device_groups(db: Session, owner_id: int):
    return db.query(DeviceGroup).filter(DeviceGroup.owner_id == owner_id).all()


def check_device_shared_with_user(db, device_id, user_id):
    return db.query(SharedDevice).filter(
        SharedDevice.device_id == device_id, SharedDevice.shared_with_id == user_id
    ).first()

def get_device_locations(db, device_id, limit=10):
    return db.query(Location).filter(
        Location.device_id == device_id
    ).order_by(Location.timestamp.desc()).limit(limit).all()

def get_device_latest_location(db, device_id):
    return db.query(Location).filter(
        Location.device_id == device_id
    ).order_by(Location.timestamp.desc()).first()

def get_user_groups(db, user_id):
    return db.query(DeviceGroup).filter(DeviceGroup.owner_id == user_id).all()

def get_device_group(db, group_id):
    return db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()

def update_device_group(db, group_id, group):
    db.query(DeviceGroup).filter(DeviceGroup.id == group_id).update(group)
    db.commit()

def delete_device_group(db, group_id):
    db.query(DeviceGroup).filter(DeviceGroup.id == group_id).delete()
    db.commit()

def remove_device_from_group(db, group_id, device_id):
    db.query(DeviceGroup).filter(
        DeviceGroup.group_id == group_id, DeviceGroup.device_id == device_id
    ).delete()
    db.commit()

def get_user_alerts(db, user_id, device_id=None, resolved=None):
    query = db.query(Alert).filter(Alert.user_id == user_id)
    if device_id:
        query = query.filter(Alert.device_id == device_id)
    if resolved is not None:
        query = query.filter(Alert.resolved == resolved)
    return query.all()

def get_alert(db, alert_id):
    return db.query(Alert).filter(Alert.id == alert_id).first()

def resolve_alert(db, alert_id):
    db.query(Alert).filter(Alert.id == alert_id).update({"resolved": True})
    db.commit()

def share_device(db, device_id, owner_id, shared_with_id, permission_level, expires_at):
    share = SharedDevice(
        device_id=device_id,
        owner_id=owner_id,
        shared_with_id=shared_with_id,
        permission_level=permission_level,
        expires_at=expires_at
    )
    db.add(share)
    db.commit()
    return share

def get_devices_shared_by_user(db, user_id):
    return db.query(SharedDevice).filter(SharedDevice.owner_id == user_id).all()

def get_devices_shared_with_user(db, user_id):
    return db.query(SharedDevice).filter(SharedDevice.shared_with_id == user_id).all()

def delete_device_share(db, share_id):
    db.query(SharedDevice).filter(SharedDevice.id == share_id).delete()
    db.commit()

def get_device_share(db, share_id):
    return db.query(SharedDevice).filter(SharedDevice.id == share_id).first()
