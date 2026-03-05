from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
import uuid

app = FastAPI()

# Подключаем папки с шаблонами и статикой (фотографиями)
templates = Jinja2Templates(directory="templates")
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Настройка базы данных SQLite
def init_db():
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS memories
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       lat
                       REAL,
                       lng
                       REAL,
                       text
                       TEXT,
                       image_path
                       TEXT
                   )
                   """)
    conn.commit()
    conn.close()


init_db()


# --- СТРАНИЦЫ ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/map", response_class=HTMLResponse)
async def read_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})


# --- API ДЛЯ КАРТЫ (Сохранение и получение воспоминаний) ---
# Добавь этот эндпоинт в main.py (например, перед @app.post("/api/add_memory"))

@app.get("/api/get_all_memories")
async def get_all_memories():
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    # Берем координаты и текст всех записей
    cursor.execute("SELECT lat, lng, text FROM memories ORDER BY id DESC")
    data = [{"lat": row[0], "lng": row[1], "text": row[2]} for row in cursor.fetchall()]
    conn.close()
    return {"memories": data}

@app.post("/api/add_memory")
async def add_memory(
        lat: float = Form(...),
        lng: float = Form(...),
        text: str = Form(...),
        file: UploadFile = File(...)
):
    # Сохраняем картинку
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"static/uploads/{unique_filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Сохраняем в базу данных
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memories (lat, lng, text, image_path) VALUES (?, ?, ?, ?)",
                   (lat, lng, text, f"/{file_path}"))
    conn.commit()
    conn.close()

    return {"status": "success"}


@app.get("/api/get_memories")
async def get_memories(lat: float, lng: float):
    # Ищем воспоминания в радиусе координат (для простоты - точное совпадение)
    conn = sqlite3.connect("memories.db")
    cursor = conn.cursor()
    cursor.execute("SELECT text, image_path FROM memories WHERE lat=? AND lng=?", (lat, lng))
    memories = [{"text": row[0], "image_path": row[1]} for row in cursor.fetchall()]
    conn.close()
    return {"memories": memories}