# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    devices = relationship("Device", back_populates="owner")
    device_groups = relationship("DeviceGroup", back_populates="owner")
    shared_to_others = relationship("SharedDevice",
                                    foreign_keys="SharedDevice.owner_id",
                                    back_populates="owner")
    shared_with_me = relationship("SharedDevice",
                                  foreign_keys="SharedDevice.shared_with_id",
                                  back_populates="shared_with")
    settings = relationship("UserSettings", back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    device_name = Column(String)
    device_type = Column(String)
    last_battery_level = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True))

    # Relationships
    owner = relationship("User", back_populates="devices")
    locations = relationship("DeviceLocation", back_populates="device")
    group_memberships = relationship("GroupMembership", back_populates="device")
    alerts = relationship("Alert", back_populates="device")
    shared = relationship("SharedDevice", back_populates="device")


class DeviceLocation(Base):
    __tablename__ = "device_locations"

    location_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.device_id"))
    latitude = Column(Float)
    longitude = Column(Float)
    accuracy = Column(Float)
    altitude = Column(Float)
    recorded_by = Column(String)  # device_id of recording device
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    device = relationship("Device", back_populates="locations")


class DeviceGroup(Base):
    __tablename__ = "device_groups"

    group_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    group_name = Column(String)
    proximity_threshold = Column(Integer, default=20)  # in meters
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="device_groups")
    memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="group")


class GroupMembership(Base):
    __tablename__ = "group_memberships"

    membership_id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("device_groups.group_id"))
    device_id = Column(String, ForeignKey("devices.device_id"))
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensure a device is only in a group once
    __table_args__ = (UniqueConstraint('group_id', 'device_id', name='_group_device_uc'),)

    # Relationships
    group = relationship("DeviceGroup", back_populates="memberships")
    device = relationship("Device", back_populates="group_memberships")


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.device_id"))
    group_id = Column(Integer, ForeignKey("device_groups.group_id"), nullable=True)
    alert_type = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_resolved = Column(Boolean, server_default=expression.false())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    device = relationship("Device", back_populates="alerts")
    group = relationship("DeviceGroup", back_populates="alerts")


class SharedDevice(Base):
    __tablename__ = "shared_devices"

    share_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.device_id"))
    owner_id = Column(Integer, ForeignKey("users.user_id"))
    shared_with_id = Column(Integer, ForeignKey("users.user_id"))
    permission_level = Column(String, default="view")  # view, locate, full
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Ensure a device is shared with a user only once
    __table_args__ = (UniqueConstraint('device_id', 'shared_with_id', name='_device_shared_user_uc'),)

    # Relationships
    device = relationship("Device", back_populates="shared")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="shared_to_others")
    shared_with = relationship("User", foreign_keys=[shared_with_id], back_populates="shared_with_me")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    token_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    token = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_revoked = Column(Boolean, default=False)


class UserSettings(Base):
    __tablename__ = "user_settings"

    setting_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    setting_key = Column(String)
    setting_value = Column(String)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Ensure a user has each setting only once
    __table_args__ = (UniqueConstraint('user_id', 'setting_key', name='_user_setting_key_uc'),)

    # Relationships
    user = relationship("User", back_populates="settings")

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    latitude = Column(String)
    longitude = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="locations")