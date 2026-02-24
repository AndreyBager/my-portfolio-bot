from fastapi import FastAPI
from database import async_session, Item
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Разрешаем доступ к API из браузера (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/items")
async def get_all_items():
    async with async_session() as session:
        result = await session.execute(select(Item))
        items = result.scalars().all()
        # Превращаем объекты базы в список словарей для сайта
        return [
            {"id": i.id, "name": i.name, "description": i.description, "category": i.category} 
            for i in items
        ]

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)