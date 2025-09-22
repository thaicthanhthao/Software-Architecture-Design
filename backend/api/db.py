# backend/api/db.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "dbname=news user=postgres password=postgres host=postgres port=5432",
)

def get_conn():
    return psycopg2.connect(POSTGRES_DSN, cursor_factory=RealDictCursor)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'reader', -- reader | reporter | admin
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    # extension for gen_random_uuid if not present
    cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # minimal seed admin if not exists (admin@local)
    cur.execute("SELECT 1 FROM users WHERE email=%s", ("admin@local",))
    exists = cur.fetchone()
    if not exists:
        from passlib.hash import bcrypt
        cur.execute(
            "INSERT INTO users(email, password_hash, role) VALUES (%s, %s, %s)",
            ("admin@local", bcrypt.hash("Admin@123"), "admin"),
        )
    conn.commit()
    cur.close()
    conn.close()
