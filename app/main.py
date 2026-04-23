from fastapi import FastAPI
from app.routes import dispositivos
from app.routes import servicios
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.include_router(dispositivos.router)
app.include_router(servicios.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)