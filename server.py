from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
import uvicorn
import asyncio
import threading

# Импорты из твоих файлов
from database import async_session, Item, delete_item_from_db
from bot import main as start_bot 

app = FastAPI()

# Разрешаем запросы (CORS), чтобы админка работала без ошибок
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

# Получение всех работ для админки
@app.get("/items")
async def get_all_items():
    async with async_session() as session:
        result = await session.execute(select(Item))
        items = result.scalars().all()
        return [
            {
                "id": i.id, 
                "name": i.name, 
                "description": i.description, 
                "category": i.category,
                "photo_id": i.photo_id  # Теперь фото тоже передается в админку
            } 
            for i in items
        ]

# Маршрут для удаления через админку
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    await delete_item_from_db(item_id)
    return {"status": "success"}

# Маршрут для редактирования (PATCH)
@app.patch("/items/{item_id}")
async def update_item(item_id: int, data: dict = Body(...)):
    async with async_session() as session:
        async with session.begin():
            item = await session.get(Item, item_id)
            if item:
                if "name" in data:
                    item.name = data["name"]
                if "description" in data:
                    item.description = data["description"]
                await session.commit() # Фиксируем изменения
                return {"status": "updated"}
            return {"status": "error", "message": "Item not found"}

# --- ЗАПУСК БОТА ВНУТРИ СЕРВЕРА ---

def run_bot():
    # Создаем новый цикл событий для потока бота
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

@app.on_event("startup")
async def startup_event():
    # Запускаем бота в отдельном потоке
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()

if __name__ == "__main__":
    # Порт 10000 для Render
    uvicorn.run(app, host="0.0.0.0", port=10000)
