from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List, Optional
from pathlib import Path

DB_PATH = Path("/app/data/todo.db")

app = FastAPI(title="ToDo Service")


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False


class Todo(TodoCreate):
    id: int


def get_connection():
    return sqlite3.connect(DB_PATH)


@app.on_event("startup")
def startup():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.post("/items", response_model=Todo)
def create_item(item: TodoCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
        (item.title, item.description, item.completed)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return Todo(id=item_id, **item.dict())


@app.get("/items", response_model=List[Todo])
def get_items():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos")
    rows = cursor.fetchall()
    conn.close()
    return [Todo(id=r[0], title=r[1], description=r[2], completed=bool(r[3])) for r in rows]


@app.get("/items/{item_id}", response_model=Todo)
def get_item(item_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, completed FROM todos WHERE id=?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return Todo(id=row[0], title=row[1], description=row[2], completed=bool(row[3]))


@app.put("/items/{item_id}", response_model=Todo)
def update_item(item_id: int, item: TodoCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE todos SET title=?, description=?, completed=?
        WHERE id=?
    """, (item.title, item.description, item.completed, item_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    conn.commit()
    conn.close()
    return Todo(id=item_id, **item.dict())


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE id=?", (item_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    conn.commit()
    conn.close()
    return {"status": "deleted"}
