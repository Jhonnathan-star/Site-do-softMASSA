import bcrypt
import uuid
from datetime import datetime, timedelta

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password: str, hashed: bytes) -> bool:
    if isinstance(hashed, str):
        hashed = hashed.encode()
    return bcrypt.checkpw(password.encode(), hashed)

def gerar_token() -> str:
    return str(uuid.uuid4())

def salvar_token(usuario_id: int, conn, dias_validade=7) -> str:
    token = gerar_token()
    criado_em = datetime.now()
    expiracao = criado_em + timedelta(days=dias_validade)

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessao_tokens (usuario_id, token, criado_em, expirado, expiracao)
        VALUES (%s, %s, %s, %s, %s)
    """, (usuario_id, token, criado_em, False, expiracao))
    conn.commit()
    cursor.close()
    return token

def validar_token(token: str, conn):
    cursor = conn.cursor()
    agora = datetime.now()
    cursor.execute("""
        SELECT usuario_id FROM sessao_tokens
        WHERE token = %s AND expirado = FALSE AND (expiracao IS NULL OR expiracao > %s)
    """, (token, agora))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado[0] if resultado else None

def marcar_token_expirado(token: str, conn):
    cursor = conn.cursor()
    cursor.execute("UPDATE sessao_tokens SET expirado = TRUE WHERE token = %s", (token,))
    conn.commit()
    cursor.close()
