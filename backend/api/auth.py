# backend/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from passlib.hash import bcrypt
from db import get_conn
from security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = Field(default="reader", pattern="^(reader|reporter|admin)$")

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(body: RegisterIn):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (body.email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    pwd_hash = bcrypt.hash(body.password)
    cur.execute(
        "INSERT INTO users(email, password_hash, role) VALUES (%s,%s,%s) RETURNING id",
        (body.email, pwd_hash, body.role),
    )
    uid = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    token = create_access_token(str(uid), body.role)
    return {"access_token": token, "token_type": "bearer", "user_id": str(uid), "role": body.role}

@router.post("/login")
def login(body: LoginIn):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash, role FROM users WHERE email=%s", (body.email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row or not bcrypt.verify(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Sai email hoặc mật khẩu")
    token = create_access_token(str(row["id"]), row["role"])
    return {"access_token": token, "token_type": "bearer", "user_id": str(row["id"]), "role": row["role"]}
