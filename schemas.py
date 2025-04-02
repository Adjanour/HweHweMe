from datetime import datetime
from symtable import Class

from pydantic import BaseModel, EmailStr
from typing import Optional, Dict


class LatLon(BaseModel):
    latitude: float
    longitude: float


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DeviceCreate(BaseModel):
    name: str
    ble_id: str
    last_location: Dict


class LocationResponse(BaseModel):
    lat: float
    lon: float

    class Config:
        orm_mode = True

class DeviceResponse(BaseModel):
    id: int
    user_id: int
    name: str
    ble_id: str
    last_location: Optional[LocationResponse] = None  # Optional in case no location is set
    last_seen: datetime

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "name": "HweHweMe Tag 1",
                "ble_id": "unique_ble_id_123",
                "last_location": {"lat": 37.7749, "lon": -122.4194},
                "last_seen": "2023-10-01T12:00:00"
            }
        }


class GroupCreate(BaseModel):
    name: str

class LocationCreate(BaseModel):
    device_id: int
    gps_location: dict  # {lat: float, lon: float}
    signal_strength: Optional[int] = None