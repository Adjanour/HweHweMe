# schemas.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    user_id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# Device schemas
class DeviceBase(BaseModel):
    device_name: str
    device_type: str


class DeviceCreate(DeviceBase):
    device_id: str


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    last_battery_level: Optional[int] = None


class Device(DeviceBase):
    device_id: str
    user_id: int
    last_battery_level: Optional[int] = None
    created_at: datetime
    last_active: Optional[datetime] = None

    class Config:
        orm_mode = True


# Location schemas
class DeviceLocationBase(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None


class DeviceLocationCreate(DeviceLocationBase):
    device_id: str
    recorded_by: Optional[str] = None  # device_id that reported this location


class DeviceLocation(DeviceLocationBase):
    location_id: int
    device_id: str
    recorded_by: Optional[str] = None
    timestamp: datetime

    class Config:
        orm_mode = True


# Device group schemas
class DeviceGroupBase(BaseModel):
    group_name: str
    proximity_threshold: Optional[int] = 20  # default 20 meters


class DeviceGroupCreate(DeviceGroupBase):
    pass


class DeviceGroupUpdate(BaseModel):
    group_name: Optional[str] = None
    proximity_threshold: Optional[int] = None


class DeviceGroup(DeviceGroupBase):
    group_id: int
    user_id: int
    created_at: datetime
    devices: List[str] = []  # List of device_ids in the group

    class Config:
        orm_mode = True


# Group membership schema
class GroupMembershipBase(BaseModel):
    group_id: int
    device_id: str


class GroupMembershipCreate(GroupMembershipBase):
    pass


class GroupMembership(GroupMembershipBase):
    membership_id: int
    added_at: datetime

    class Config:
        orm_mode = True


# Alert schemas
class AlertBase(BaseModel):
    device_id: str
    alert_type: str
    group_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AlertCreate(AlertBase):
    pass


class Alert(AlertBase):
    alert_id: int
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Shared device schemas
class SharedDeviceBase(BaseModel):
    device_id: str
    permission_level: str = "view"  # view, locate, full
    expires_at: Optional[datetime] = None


class SharedDeviceCreate(SharedDeviceBase):
    shared_with_email: EmailStr


class SharedDevice(BaseModel):
    share_id: int
    device_id: str
    owner_id: int
    shared_with_id: int
    permission_level: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    device_name: Optional[str] = None  # For displaying in UI
    owner_name: Optional[str] = None  # For displaying in UI

class DeviceBase(BaseModel):
    name: str

class DeviceResponse(DeviceBase):
    id: int
    user_id: int
    is_active: bool
    class Config:
        orm_mode = True

class LocationBase(BaseModel):
    latitude: str
    longitude: str

class LocationCreate(LocationBase):
    device_id: int

class LocationResponse(LocationBase):
    id: int
    device_id: int
    timestamp: datetime
    class Config:
        orm_mode = True