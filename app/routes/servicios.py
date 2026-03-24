from fastapi import APIRouter
import pymysql
from app.database import get_connection
from app.schemas import Servicios

router = APIRouter()

@router.get("/dispositivos/{serial_number}/servicios")
def obtener_servicios_dispositivo(serial_number: str):

    connection = get_connection()

    with connection.cursor(pymysql.cursors.DictCursor) as cursor:

        cursor.execute(
            "SELECT * FROM servicios WHERE serial_number=%s",
            (serial_number,)
        )

        Servicios = cursor.fetchall()

    connection.close()

    return Servicios
        
        
        
@router.post("/servicios")
def registrar_servicio(data: Servicios):

    connection = get_connection()

    with connection.cursor(pymysql.cursors.DictCursor) as cursor:

        sql = """
        INSERT INTO servicios (
            serial_number,
            fecha,
            persona_responsable,
            estado,
            descripcion,
            observaciones
        )
        VALUES (%s,%s,%s,%s,%s,%s )
        """

        cursor.execute(sql, (
            data.serial_number,
            data.fecha,
            data.persona_responsable,
            data.estado,
            data.descripcion,
            data.observaciones
        ))

        connection.commit()

    connection.close()

    return {"message": "Servicio registrado exitosamente"}