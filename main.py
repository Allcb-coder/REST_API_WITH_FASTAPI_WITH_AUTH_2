from fastapi import FastAPI, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import Optional, List
import crud
from database import get_db, create_tables
from schemas import (
    UserCreate, UserResponse, UserUpdate,
    AdvertisementCreate, AdvertisementResponse, AdvertisementUpdate,
    LoginRequest, TokenResponse
)
from auth import create_access_token, verify_token
from models import User, UserRole
from datetime import datetime, timedelta

# Create tables
create_tables()

app = FastAPI(
    title="Advertisement Service Part 2",
    description="REST API for advertisement management with authentication",
    version="2.0.0"
)


# Basic endpoints
@app.get("/")
def read_root():
    return {"message": "Advertisement Service Part 2 is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Authentication Dependency
async def get_current_user(
        authorization: str = Header(None),
        db: Session = Depends(get_db)
) -> Optional[User]:
    print(f"🔐 DEBUG: Authorization header: {authorization}")

    if authorization is None:
        print("❌ DEBUG: No authorization header provided")
        return None

    # Extract token from "Bearer <token>"
    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            print("❌ DEBUG: Invalid authorization format")
            return None

        token = parts[1]
        print(f"✅ DEBUG: Extracted token: {token[:50]}...")
    except Exception as e:
        print(f"❌ DEBUG: Error extracting token: {e}")
        return None

    # Verify the token
    payload = verify_token(token)
    if payload is None:
        print("❌ DEBUG: Token verification failed")
        return None

    username: str = payload.get("sub")
    if username is None:
        print("❌ DEBUG: No username in token payload")
        return None

    user = crud.get_user_by_username(db, username=username)
    if user is None:
        print("❌ DEBUG: User not found in database")
        return None

    print(f"✅ DEBUG: Authentication successful for user: {username}")
    return user


async def get_current_active_user(current_user: Optional[User] = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# User endpoints
@app.post("/user", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user (available to unauthenticated users)
    """
    # Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return crud.create_user(db=db, user=user)


@app.get("/user/{user_id}", response_model=UserResponse)
def get_user(
        user_id: int,
        current_user: Optional[User] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get user by ID (available to unauthenticated users)
    """
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.patch("/user/{user_id}", response_model=UserResponse)
def update_user(
        user_id: int,
        user_update: UserUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Update user (users can update themselves, admins can update anyone)
    """
    # Check permissions
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user"
        )

    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/user/{user_id}")
def delete_user(
        user_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Delete user (users can delete themselves, admins can delete anyone)
    """
    # Check permissions
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this user"
        )

    success = crud.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


# Advertisement endpoints
@app.post("/advertisement", response_model=AdvertisementResponse)
def create_advertisement(
        advertisement: AdvertisementCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Create new advertisement (authenticated users only)
    """
    print(f"✅ Creating advertisement for user: {current_user.username}")
    return crud.create_advertisement(db=db, advertisement=advertisement, owner_id=current_user.id)


@app.get("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
def get_advertisement(
        advertisement_id: int,
        current_user: Optional[User] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get advertisement by ID (available to unauthenticated users)
    """
    db_advertisement = crud.get_advertisement(db, advertisement_id=advertisement_id)
    if db_advertisement is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return db_advertisement


@app.patch("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
def update_advertisement(
        advertisement_id: int,
        advertisement_update: AdvertisementUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Update advertisement (owners can update their ads, admins can update any)
    """
    db_advertisement = crud.get_advertisement(db, advertisement_id=advertisement_id)
    if db_advertisement is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    # Check ownership or admin
    if db_advertisement.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this advertisement"
        )

    return crud.update_advertisement(db, advertisement_id=advertisement_id, advertisement_update=advertisement_update)


@app.delete("/advertisement/{advertisement_id}")
def delete_advertisement(
        advertisement_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Delete advertisement (owners can delete their ads, admins can delete any)
    """
    db_advertisement = crud.get_advertisement(db, advertisement_id=advertisement_id)
    if db_advertisement is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    # Check ownership or admin
    if db_advertisement.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this advertisement"
        )

    success = crud.delete_advertisement(db, advertisement_id=advertisement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return {"message": "Advertisement deleted successfully"}


@app.get("/advertisement", response_model=List[AdvertisementResponse])
def search_advertisements(
        title: Optional[str] = Query(None, description="Search in title"),
        description: Optional[str] = Query(None, description="Search in description"),
        min_price: Optional[float] = Query(None, description="Minimum price"),
        max_price: Optional[float] = Query(None, description="Maximum price"),
        current_user: Optional[User] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Search advertisements (available to unauthenticated users)
    """
    return crud.search_advertisements(
        db=db,
        title=title,
        description=description,
        min_price=min_price,
        max_price=max_price
    )


# Authentication endpoints
@app.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token
    """
    user = crud.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)