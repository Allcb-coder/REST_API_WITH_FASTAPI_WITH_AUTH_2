from sqlalchemy.orm import Session
from models import User, Advertisement, UserRole
from schemas import UserCreate, UserUpdate, AdvertisementCreate, AdvertisementUpdate
from auth import get_password_hash, verify_password
from typing import List, Optional


# User CRUD operations
def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    db_user = get_user_by_id(db, user_id)
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# Advertisement CRUD operations
def create_advertisement(db: Session, advertisement: AdvertisementCreate, owner_id: int) -> Advertisement:
    db_advertisement = Advertisement(
        **advertisement.model_dump(),
        owner_id=owner_id
    )
    db.add(db_advertisement)
    db.commit()
    db.refresh(db_advertisement)
    return db_advertisement


def get_advertisement(db: Session, advertisement_id: int) -> Optional[Advertisement]:
    return db.query(Advertisement).filter(Advertisement.id == advertisement_id).first()


def update_advertisement(db: Session, advertisement_id: int, advertisement_update: AdvertisementUpdate) -> Optional[
    Advertisement]:
    db_advertisement = get_advertisement(db, advertisement_id)
    if db_advertisement:
        update_data = advertisement_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_advertisement, field, value)
        db.commit()
        db.refresh(db_advertisement)
    return db_advertisement


def delete_advertisement(db: Session, advertisement_id: int) -> bool:
    db_advertisement = get_advertisement(db, advertisement_id)
    if db_advertisement:
        db.delete(db_advertisement)
        db.commit()
        return True
    return False


def search_advertisements(
        db: Session,
        title: Optional[str] = None,
        description: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
) -> List[Advertisement]:
    query = db.query(Advertisement)

    if title:
        query = query.filter(Advertisement.title.contains(title))
    if description:
        query = query.filter(Advertisement.description.contains(description))
    if min_price is not None:
        query = query.filter(Advertisement.price >= min_price)
    if max_price is not None:
        query = query.filter(Advertisement.price <= max_price)

    return query.all()