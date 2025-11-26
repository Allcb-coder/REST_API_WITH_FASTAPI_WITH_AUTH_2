from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

# Security configuration - THIS MATCHES THE .env FILE
SECRET_KEY = os.getenv("SECRET_KEY", "Tm9Y0-QugrOVirWQ-kplU2sdDwprIFFeSvZUJV__r2A")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 48

print(f"🔑 DEBUG: Using SECRET_KEY: {SECRET_KEY[:20]}...")


# Password hashing
def safe_bcrypt_hash(password: str) -> str:
    """Hash password with bcrypt, safely handling long passwords"""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')


def safe_bcrypt_verify(plain_password: str, hashed_password: str) -> bool:
    """Verify password with bcrypt, safely handling long passwords"""
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return safe_bcrypt_verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return safe_bcrypt_hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"🔑 DEBUG: Created token with secret: {SECRET_KEY[:20]}...")
    return encoded_jwt


def verify_token(token: str):
    try:
        print(f"🔑 DEBUG: Verifying token with secret: {SECRET_KEY[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ DEBUG: Token verified successfully")
        return payload
    except JWTError as e:
        print(f"❌ DEBUG: Token verification failed: {e}")
        return None