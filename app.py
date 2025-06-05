import streamlit as st
from database.connection import conectar
from modules.inserir_telas import inserir_telas
from modules.processa_turno import inserir_horarios_separados_front, buscar_historico_por_data
from modules.predicao import criar_predicao_semana
from modules.ver_alterar import ver_e_alterar_telas_por_data
from modules.pedidos import inserir_pedidos_automatizado, inserir_pedidos_manual
from pages.login import login_usuario, cadastrar_usuario  # IMPORTAÇÃO AQUI

# Configuração da página
st.set_page_config(page_title="Sistema de Padaria", layout="centered")

# Inicializa estado de login
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# Login e Cadastro
if not st.session_state.logado:
    st.title("🔐 Acesso ao softMASSA")
    aba = st.sidebar.selectbox("Ação", ["Login", "Cadastro"])
    conn = conectar()
    if conn:
        if aba == "Login":
            login_usuario(conn)
        else:
            cadastrar_usuario(conn)
        conn.close()
    else:
        st.error("Erro ao conectar ao banco de dados.")
    st.stop()  # Para execução aqui se não estiver logado

# Se logado, segue para o menu principal
if "pagina" not in st.session_state:
    st.session_state.pagina = "menu"

# Menu principal e navegação lateral
if st.session_state.pagina == "menu":
    st.title("🍞 Sistema da softMASSA")
    st.success(f"Bem-vindo, {st.session_state.usuario}!")
    opcao = st.sidebar.selectbox("Selecione uma opção:", [
        "Inserir dados de telas",
        "Inserir somente horários",
        "Criar predição da semana",
        "Ver/Alterar dados das telas",
        "Buscar relatório por data",
        "Previsão automática de pedidos",
        "Previsão manual de pedidos",
        "Sair"
    ])

    if st.button("Selecionar"):
        st.session_state.pagina = opcao

# Páginas
def executar_pagina(funcao):
    conn = conectar()
    if not conn:
        st.error("❌ Não foi possível conectar ao banco de dados.")
    else:
        try:
            funcao(conn)
        finally:
            conn.close()
    if st.button("🔙 Voltar ao menu"):
        st.session_state.pagina = "menu"

if st.session_state.pagina == "Inserir dados de telas":
    executar_pagina(inserir_telas)

elif st.session_state.pagina == "Inserir somente horários":
    executar_pagina(inserir_horarios_separados_front)

elif st.session_state.pagina == "Criar predição da semana":
    executar_pagina(criar_predicao_semana)

elif st.session_state.pagina == "Ver/Alterar dados das telas":
    executar_pagina(ver_e_alterar_telas_por_data)

elif st.session_state.pagina == "Buscar relatório por data":
    executar_pagina(buscar_historico_por_data)

elif st.session_state.pagina == "Previsão automática de pedidos":
    executar_pagina(inserir_pedidos_automatizado)

elif st.session_state.pagina == "Previsão manual de pedidos":
    executar_pagina(inserir_pedidos_manual)

elif st.session_state.pagina == "Sair":
    st.session_state.clear()
    st.write("👋 Você saiu do sistema. Feche a aba do navegador para encerrar a sessão.")
    st.stop()




# Aqui você pode adicionar os outros blocos elif para outras opções, como:
# elif st.session_state.pagina == "Ver/Alterar dados das telas":
#    ...
# elif st.session_state.pagina == "Buscar relatório por data":
#    ...
# etc.

