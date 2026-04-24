import os
import uuid
import pymysql
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles   # se monta en main.py
from app.database import get_connection
from app.schemas import Dispositivo, CrearDispositivo, ActualizarDispositivo

router = APIRouter()

# ── Carpeta donde se guardan las fotos ──────────────────────────────────────
UPLOAD_DIR = "uploads/fotos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_SIZE_MB = 5


# ── Subir / reemplazar foto de un dispositivo ────────────────────────────────
@router.post("/dispositivos/{serial_number}/foto")
async def subir_foto(serial_number: str, file: UploadFile = File(...)):
    """
    Sube una imagen y guarda la ruta relativa en la columna `foto`.
    Endpoint: POST /dispositivos/{serial_number}/foto
    Form-data: file (imagen)
    """
    # Validar extensión
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido. Usa: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Leer contenido y validar tamaño
    content = await file.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {MAX_SIZE_MB} MB"
        )

    # Nombre único para el archivo
    filename  = f"{uuid.uuid4().hex}{ext}"
    filepath  = os.path.join(UPLOAD_DIR, filename)
    foto_url  = f"/uploads/fotos/{filename}"   # URL pública

    # Guardar archivo en disco
    with open(filepath, "wb") as f:
        f.write(content)

    # Actualizar columna foto en BD (y borrar foto anterior si existe)
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtener foto anterior para borrarla del disco
            cursor.execute(
                "SELECT foto FROM dispositivos WHERE serial_number = %s",
                (serial_number,)
            )
            row = cursor.fetchone()
            if row and row.get("foto"):
                old_path = row["foto"].lstrip("/")   # quitar "/" inicial
                if os.path.exists(old_path):
                    os.remove(old_path)

            cursor.execute(
                "UPDATE dispositivos SET foto = %s WHERE serial_number = %s",
                (foto_url, serial_number)
            )
            connection.commit()
        connection.close()
    except Exception as e:
        # Si falla la BD, borrar el archivo recién creado
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=str(e))

    return {"foto": foto_url, "message": "Foto subida correctamente"}


# ── Listar todos los dispositivos ────────────────────────────────────────────
@router.get("/dispositivos")
def obtener_dispositivos():
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    d.*,
                    u.name      AS user_name,
                    u.apellido  AS user_apellido,
                    u.rol       AS user_rol
                FROM dispositivos d
                LEFT JOIN users u ON d.id_user = u.id
            """)
            dispositivos = cursor.fetchall()
        connection.close()
        return dispositivos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Buscar dispositivos por nombre de usuario ─────────────────────────────────
@router.get("/usuarios/{name}/{apellido}/dispositivos")
def obtener_dispositivos_por_usuario(name: str, apellido: str):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT d.*, u.name AS user_name, u.apellido AS user_apellido
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


# ── Obtener un dispositivo por serial (incluye servicios) ────────────────────
@router.get("/dispositivos/{serial_number}")
def obtener_dispositivo(serial_number: str):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT
                    d.*,
                    u.name      AS user_name,
                    u.apellido  AS user_apellido,
                    u.rol       AS user_rol
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


# ── Crear dispositivo ─────────────────────────────────────────────────────────
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

            sql = """
            INSERT INTO dispositivos (
                serial_number, tipo, marca, modelo,
                nombre_dispositivo, ubicacion,
                imei, imei2, numero_linea, color,
                almacenamiento, ram, sistema_operativo,
                fecha_compra, estado, propietario, id_user
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data.serial_number,
                data.tipo,
                data.marca,
                data.modelo,
                data.nombre_dispositivo or None,
                data.ubicacion or None,
                data.imei or None,
                data.imei2 or None,
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


# ── Actualizar dispositivo ────────────────────────────────────────────────────
@router.put("/dispositivos/{serial_number}")
def actualizar_dispositivo(serial_number: str, data: ActualizarDispositivo):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:

            data_dict = data.model_dump(exclude_unset=True)
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


# ── Eliminar dispositivo ──────────────────────────────────────────────────────
@router.delete("/dispositivos/{serial_number}")
def eliminar_dispositivo(serial_number: str):
    try:
        connection = get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Borrar foto del disco si existe
            cursor.execute(
                "SELECT foto FROM dispositivos WHERE serial_number = %s",
                (serial_number,)
            )
            row = cursor.fetchone()
            if row and row.get("foto"):
                old_path = row["foto"].lstrip("/")
                if os.path.exists(old_path):
                    os.remove(old_path)

            cursor.execute(
                "DELETE FROM dispositivos WHERE serial_number = %s",
                (serial_number,)
            )
            connection.commit()
        connection.close()
        return {"message": "Dispositivo eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))