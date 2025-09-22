# backend/api/security.py
import os
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("JWT_SECRET", "change-this-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(sub: str, role: str):
    payload = {
        "sub": sub,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"id": payload["sub"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token hết hạn")
    except Exception:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

def require_roles(*roles):
    def checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện")
        return user
    return checker
