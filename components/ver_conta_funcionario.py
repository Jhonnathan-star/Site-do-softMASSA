import streamlit as st
from database.connection import conectar
from components.conta import visualizar_contas
from components.faltas import visualizar_faltas

def ver_conta_funcionario(conn):
    st.subheader("👤 Ver Conta de Funcionário")
    cursor = conn.cursor()

    id_usuario_logado = st.session_state.get("usuario_id")
    tipo_usuario = st.session_state.get("usuario_tipo", "comum")

    # Selecionar funcionário
    if tipo_usuario == "admin":
        cursor.execute("SELECT id, usuario FROM usuarios ORDER BY usuario")
        usuarios = cursor.fetchall()

        if not usuarios:
            st.warning("Nenhum usuário encontrado.")
            return

        nomes_usuarios = [u[1] for u in usuarios]
        nome_selecionado = st.selectbox("Selecione o funcionário:", nomes_usuarios)
        id_usuario_selecionado = next(u[0] for u in usuarios if u[1] == nome_selecionado)
    else:
        id_usuario_selecionado = id_usuario_logado
        nome_selecionado = st.session_state.get("usuario", "Usuário")

    # Caixa de seleção (visão: conta ou falta)
    tipo_visualizacao = st.radio("Visualizar:", ["Contas", "Faltas"])

    if tipo_visualizacao == "Contas":
        visualizar_contas(conn, id_usuario_selecionado, nome_selecionado, tipo_usuario)
    else:
        visualizar_faltas(conn, id_usuario_selecionado, nome_selecionado, tipo_usuario)
