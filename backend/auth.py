from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Depends, status
from sqlalchemy.orm import Session
from backend.schemas import UserPublic
from backend.models import User
from typing import Optional
from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from backend.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, hashed_password: str):
    existing = db.query(User).filter(User.username==username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username unavailable")
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409,detail="Username unavailable")
    db.refresh(user)
    return user

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    print(data)
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    print(to_encode, jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

dummy=hash_password('dummypassword')
def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        verify_password(password, dummy)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)          # ✅ inject db
) -> UserPublic:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = get_user(db, username)          # ✅ pass db
    if not user:
        raise cred_exc
    return UserPublic(username=user.username)  # ✅ attribute access


def get_username_from_cookie(request: Request) -> Optional[str]:
    token = request.cookies.get("access_token")
    print(token)
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def get_username_from_header(request:Request)->Optional[str]:
    auth_header = request.headers.get("Authorization")
    for i in request.headers:
        print(i)
    # print('request',request)
    print('auth header',auth_header)
    if not auth_header or not auth_header.startswith("Bearer"):
        return None
    token = auth_header.split(" ")[1]
    # print('token from header',token)
    try:
        payload = jwt.decode(token,SECRET_KEY,  algorithms=[ALGORITHM])
        return payload.get("sub")
        # print('payload',payload)
    except JWTError:
        return None
