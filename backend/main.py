from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.generate import router as generate_router

app = FastAPI(title="Paper2Notebook API", version="0.1.0")
app.include_router(generate_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}
