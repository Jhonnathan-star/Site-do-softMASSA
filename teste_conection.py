import mysql.connector
from mysql.connector import Error

try:
    # Dados de conexão (substitua pela sua senha real se necessário)
    connection = mysql.connector.connect(
        host='turntable.proxy.rlwy.net',
        port=43507,
        user='root',
        password='WNApvlyvcMKaUgEyhwrUZWuAHMDlhmAT',  # Coloque a senha do Railway
        database='railway'
    )

    if connection.is_connected():
        db_info = connection.get_server_info()
        print("✅ Conectado ao servidor MySQL versão:", db_info)
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        record = cursor.fetchone()
        print("📂 Banco de dados em uso:", record)

except Error as e:
    print("❌ Erro ao conectar ao MySQL:", e)

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("🔌 Conexão encerrada.")