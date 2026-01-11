from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import sqlite3
import string
import random
from pathlib import Path

DB_PATH = Path("/app/data/shorturl.db")

app = FastAPI(title="Short URL Service")


class URLCreate(BaseModel):
    url: str


def get_connection():
    return sqlite3.connect(DB_PATH)


def generate_short_id(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


@app.on_event("startup")
def startup():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            short_id TEXT PRIMARY KEY,
            full_url TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.post("/shorten")
def shorten_url(data: URLCreate):
    short_id = generate_short_id()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO urls (short_id, full_url) VALUES (?, ?)",
        (short_id, data.url)
    )
    conn.commit()
    conn.close()
    return {"short_url": f"/{short_id}", "short_id": short_id}


@app.get("/{short_id}")
def redirect(short_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_url FROM urls WHERE short_id=?", (short_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(row[0])


@app.get("/stats/{short_id}")
def stats(short_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_url FROM urls WHERE short_id=?", (short_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"short_id": short_id, "full_url": row[0]}
