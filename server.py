from fastapi import FastAPI
from fastapi.responses import FileResponse
from database import async_session, Item
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import threading
from bot import main as start_bot # Импортируем функцию запуска бота

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

@app.get("/items")
async def get_all_items():
    async with async_session() as session:
        result = await session.execute(select(Item))
        items = result.scalars().all()
        return [
            {"id": i.id, "name": i.name, "description": i.description, "category": i.category} 
            for i in items
        ]

# Функция для запуска бота в отдельном потоке
def run_bot():
    asyncio.run(start_bot())

@app.on_event("startup")
async def startup_event():
    # Запускаем бота, когда стартует сервер
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
