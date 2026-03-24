from fastapi import APIRouter
from app.database import get_connection

router = APIRouter()

@router.get("/usuarios")
def obtener_usuarios():
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        usuarios = cursor.fetchall()

    connection.close()

    return usuarios

