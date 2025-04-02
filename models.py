from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, LargeBinary
from geoalchemy2 import Geography
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    ble_id = Column(String, unique=True, index=True)
    last_location = Column(Geography('POINT', srid=4326))
    last_seen = Column(DateTime, default=datetime.utcnow)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GroupDevice(Base):
    __tablename__ = "group_devices"

    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), primary_key=True)

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    gps_location = Column(Geography('POINT', srid=4326))
    signal_strength = Column(Integer)