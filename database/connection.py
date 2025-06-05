import mysql.connector
from mysql.connector import Error

def conectar():
    try:
        conn = mysql.connector.connect(
            host='turntable.proxy.rlwy.net',
            port=43507,
            user='root',
            password='WNApvlyvcMKaUgEyhwrUZWuAHMDlhmAT',
            database='railway'
        )
        if conn.is_connected():
            print("Conexão bem-sucedida ao banco de dados")
            return conn
    except Error as e:
        print(f"Erro ao conectar: {e}")
        return None
