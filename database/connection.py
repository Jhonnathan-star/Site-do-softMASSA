import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Carrega as variáveis do .env
load_dotenv()

def conectar():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        if conn.is_connected():
            print("Conexão bem-sucedida ao banco de dados")
            return conn
    except Error as e:
        print(f"Erro ao conectar: {e}")
        return None

