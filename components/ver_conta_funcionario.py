import streamlit as st
from database.connection import conectar
from components.conta import visualizar_contas
from components.faltas import visualizar_faltas
from components.extras import visualizar_extras

def ver_conta_funcionario(conn):
    st.markdown("<h2 style='margin-bottom: 30px;'>👤 Ver Conta de Funcionário</h2>", unsafe_allow_html=True)

    cursor = conn.cursor()
    id_usuario_logado = st.session_state.get("usuario_id")
    tipo_usuario = st.session_state.get("usuario_tipo", "comum")

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

    if "tipo_visualizacao" not in st.session_state:
        st.session_state.tipo_visualizacao = None

    st.markdown("<h4 style='margin-top: 40px;'>🔎 Escolha o que deseja visualizar:</h4>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💰 Contas"):
            st.session_state.tipo_visualizacao = "Contas"
    with col2:
        if st.button("📋 Faltas"):
            st.session_state.tipo_visualizacao = "Faltas"
    with col3:
        if st.button("🕒 Extras"):
            st.session_state.tipo_visualizacao = "Extras"
    with col4:
        if st.button("📊 Todos os dados"):
            st.session_state.tipo_visualizacao = "Todos"

    if st.session_state.tipo_visualizacao:
        tipo_visualizacao = st.session_state.tipo_visualizacao

        if tipo_visualizacao == "Contas":
            visualizar_contas(conn, id_usuario_selecionado, nome_selecionado, tipo_usuario)
        elif tipo_visualizacao == "Faltas":
            visualizar_faltas(conn, id_usuario_selecionado, nome_selecionado, tipo_usuario)
        elif tipo_visualizacao == "Extras":
            visualizar_extras(conn, id_usuario_selecionado, nome_selecionado, tipo_usuario)
        elif tipo_visualizacao == "Todos":
            # Aqui fazemos as chamadas que retornam True se tem registros, False se não
            tem_contas = visualizar_contas(conn, id_usuario_selecionado, nome_selecionado, "visualizacao")
            tem_faltas = visualizar_faltas(conn, id_usuario_selecionado, nome_selecionado, "visualizacao")
            tem_extras = visualizar_extras(conn, id_usuario_selecionado, nome_selecionado, "visualizacao")


