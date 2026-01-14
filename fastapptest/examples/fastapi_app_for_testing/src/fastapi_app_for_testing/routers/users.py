# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.user import User as UserSchema, UserCreate
from models.user import User as UserModel
from core.security import hash_password

router = APIRouter()

@router.post("/", response_model=UserSchema)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    if db is None:
        raise HTTPException(500, "Database not available")
    db_user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=list[UserSchema])
def read_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    if db is None:
        return []
    return db.query(UserModel).offset(skip).limit(limit).all()

@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    if db is None:
        raise HTTPException(500, "Database not available")
    user = db.query(UserModel).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    if db is None:
        raise HTTPException(500, "Database not available")
    user = db.query(UserModel).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    user.username = user_in.username
    user.email = user_in.email
    user.hashed_password = hash_password(user_in.password)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    if db is None:
        raise HTTPException(500, "Database not available")
    user = db.query(UserModel).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    db.delete(user)
    db.commit()
    return
