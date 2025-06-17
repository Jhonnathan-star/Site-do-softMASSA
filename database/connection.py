import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def get_port(env_var_name, default=3306):
    port_str = os.getenv(env_var_name)
    try:
        return int(port_str)
    except (TypeError, ValueError):
        return default

def conectar(config=None):
    try:
        if config is None:
            config = {
                "host": os.getenv("DB_HOST_PADARIA1"),
                "port": get_port("DB_PORT_PADARIA1"),
                "user": os.getenv("DB_USER_PADARIA1"),
                "password": os.getenv("DB_PASSWORD_PADARIA1"),
                "database": os.getenv("DB_NAME_PADARIA1"),
            }
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print(f"Conectado ao banco {config['database']}")
            return conn
    except Error as e:
        print(f"Erro ao conectar: {e}")
        return None

