from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.schemas import Dispositivo, CrearDispositivo, ActualizarDispositivo
import pymysql

router = APIRouter()


@router.get("/dispositivos")
def obtener_dispositivos():
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM dispositivos")
            dispositivos = cursor.fetchall()
        connection.close()
        return dispositivos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usuarios/{name}/{apellido}/dispositivos")
def obtener_dispositivos_por_usuario(name: str, apellido: str):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT d.*
                FROM dispositivos d
                INNER JOIN users u ON d.id_user = u.id
                WHERE u.name = %s AND u.apellido = %s
            """, (name, apellido))
            dispositivos = cursor.fetchall()
        connection.close()
        return {
            "usuario": {"name": name, "apellido": apellido},
            "dispositivos": dispositivos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dispositivos/{serial_number}")
def obtener_dispositivo(serial_number: str):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT
                    d.*,
                    u.name    AS user_name,
                    u.apellido AS user_apellido,
                    u.rol      AS user_rol
                FROM dispositivos d
                LEFT JOIN users u ON d.id_user = u.id
                WHERE d.serial_number = %s
            """, (serial_number,))
            dispositivo = cursor.fetchone()

            if not dispositivo:
                connection.close()
                return {"error": "Dispositivo no encontrado"}

            cursor.execute(
                "SELECT * FROM servicios WHERE serial_number = %s",
                (serial_number,)
            )
            servicios = cursor.fetchall()

        connection.close()
        return {"dispositivo": dispositivo, "servicios": servicios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dispositivos")
def crear_dispositivo(data: CrearDispositivo):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:

            # Buscar o crear usuario
            cursor.execute(
                "SELECT id FROM users WHERE name = %s AND apellido = %s",
                (data.name, data.apellido)
            )
            usuario = cursor.fetchone()

            if not usuario:
                cursor.execute(
                    "INSERT INTO users (name, apellido, rol) VALUES (%s, %s, %s)",
                    (data.name, data.apellido, "empleado")
                )
                connection.commit()
                id_user = cursor.lastrowid
            else:
                id_user = usuario["id"]

            # Insertar dispositivo con imei2
            sql = """
            INSERT INTO dispositivos (
                serial_number,
                tipo,
                marca,
                modelo,
                imei,
                imei2,
                numero_linea,
                color,
                almacenamiento,
                ram,
                sistema_operativo,
                fecha_compra,
                estado,
                propietario,
                id_user
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data.serial_number,
                data.tipo,
                data.marca,
                data.modelo,
                data.imei   or None,
                data.imei2  or None,   # ← NUEVO
                data.numero_linea,
                data.color,
                data.almacenamiento,
                data.ram,
                data.sistema_operativo,
                data.fecha_compra,
                data.estado,
                data.propietario,
                id_user,
            ))
            connection.commit()

        connection.close()
        return {"message": "Dispositivo registrado y asignado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/dispositivos/{serial_number}")
def actualizar_dispositivo(serial_number: str, data: ActualizarDispositivo):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:

            data_dict = data.model_dump(exclude_unset=True)
            # imei2 puede enviarse como "" — lo convertimos a None para guardar NULL
            if "imei2" in data_dict and data_dict["imei2"] == "":
                data_dict["imei2"] = None

            campos  = [f"{k} = %s" for k in data_dict]
            valores = list(data_dict.values())

            if not campos:
                return {"error": "No hay datos para actualizar"}

            valores.append(serial_number)
            sql = f"UPDATE dispositivos SET {', '.join(campos)} WHERE serial_number = %s"
            cursor.execute(sql, valores)
            connection.commit()

        connection.close()
        return {"message": "Dispositivo actualizado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/dispositivos/{serial_number}")
def eliminar_dispositivo(serial_number: str):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "DELETE FROM dispositivos WHERE serial_number = %s",
                (serial_number,)
            )
            connection.commit()
        connection.close()
        return {"message": "Dispositivo eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))