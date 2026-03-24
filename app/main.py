from fastapi import FastAPI
from app.routes import dispositivos
from app.routes import servicios
app = FastAPI()

app.include_router(dispositivos.router)
app.include_router(servicios.router)



