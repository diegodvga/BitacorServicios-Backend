import pymysql

def get_connection():
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="gestion_dispositivos",
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection