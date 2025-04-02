from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import GroupCreate
from crud import create_group, add_device_to_group
from services.auth import get_current_user
from models import Group, Device, GroupDevice, User
from typing import List

router = APIRouter(
    prefix="/groups",
    tags=["groups"]
)


@router.post("/", response_model=GroupCreate)
async def create_group_endpoint(group: GroupCreate, db: Session = Depends(get_db),
                                current_user: dict = Depends(get_current_user)):
    """
    Create a new device group for the authenticated user.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_group = create_group(db, group, user.id)
    return db_group


@router.get("/", response_model=List[GroupCreate])
async def list_groups(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    List all groups for the authenticated user.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    groups = db.query(Group).filter(Group.user_id == user.id).all()
    return groups


@router.get("/{group_id}", response_model=GroupCreate)
async def get_group(group_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get details of a specific group.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group = db.query(Group).filter(Group.id == group_id, Group.user_id == user.id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return group


@router.put("/{group_id}", response_model=GroupCreate)
async def update_group(group_id: int, group: GroupCreate, db: Session = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    """
    Update a specific group.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_group = db.query(Group).filter(Group.id == group_id, Group.user_id == user.id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db_group.name = group.name
    db.commit()
    db.refresh(db_group)
    return db_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Delete a specific group.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_group = db.query(Group).filter(Group.id == group_id, Group.user_id == user.id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db.delete(db_group)
    db.commit()
    return None


@router.post("/{group_id}/devices/{device_id}", status_code=status.HTTP_201_CREATED)
async def add_device_to_group_endpoint(group_id: int, device_id: int, db: Session = Depends(get_db),
                                       current_user: dict = Depends(get_current_user)):
    """
    Add a device to a specific group.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group = db.query(Group).filter(Group.id == group_id, Group.user_id == user.id).first()
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == user.id).first()

    if not group or not device:
        raise HTTPException(status_code=404, detail="Group or Device not found")

    add_device_to_group(db, group_id, device_id)
    return {"message": "Device added to group successfully"}


@router.delete("/{group_id}/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_device_from_group(group_id: int, device_id: int, db: Session = Depends(get_db),
                                   current_user: dict = Depends(get_current_user)):
    """
    Remove a device from a specific group.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group_device = db.query(GroupDevice).filter(GroupDevice.group_id == group_id,
                                                GroupDevice.device_id == device_id).first()
    if not group_device:
        raise HTTPException(status_code=404, detail="Device not found in group")

    db.delete(group_device)
    db.commit()
    return None