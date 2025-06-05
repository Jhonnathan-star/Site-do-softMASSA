import streamlit as st
from database.connection import conectar
from modules.inserir_telas import inserir_telas
from modules.processa_turno import inserir_horarios_separados_front, buscar_historico_por_data
from modules.predicao import criar_predicao_semana
from modules.ver_alterar import ver_e_alterar_telas_por_data
from modules.pedidos import inserir_pedidos_automatizado, inserir_pedidos_manual
from pages.login import login_usuario, cadastrar_usuario

# Configuração da página
st.set_page_config(page_title="Sistema de Padaria", layout="centered")

# Constantes
SUPERUSUARIO = "Jhonnathan"

# Inicializa estados
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "menu"
if "rerun_flag" not in st.session_state:
    st.session_state.rerun_flag = False
if "logout_rerun_flag" not in st.session_state:
    st.session_state.logout_rerun_flag = False

# Conecta ao banco
conn = conectar()
if conn is None:
    st.error("Erro ao conectar ao banco de dados.")
    st.stop()

# Exibe tela de login se não estiver logado
if not st.session_state.logado:
    st.title("🔐 Acesso ao softMASSA")
    login_usuario(conn)
    conn.close()
    st.stop()

# Usuário está logado — menu principal
st.title("🍞 Sistema da softMASSA")
st.success(f"Bem-vindo, {st.session_state.usuario}!")

# Menu lateral com opções
opcoes = [
    "Inserir dados de telas",
    "Inserir somente horários",
    "Criar predição da semana",
    "Ver/Alterar dados das telas",
    "Buscar relatório por data",
    "Previsão automática de pedidos",
    "Previsão manual de pedidos",
]

# Superusuário vê a opção de cadastrar novo usuário
if st.session_state.usuario == SUPERUSUARIO:
    opcoes.append("Cadastrar novo usuário")

opcoes.append("Sair")

# Navegação do menu
opcao = st.sidebar.selectbox("Selecione uma opção:", opcoes)
if st.button("Selecionar"):
    st.session_state.pagina = opcao

# Função genérica para executar páginas
def executar_pagina(funcao):
    conn = conectar()
    if not conn:
        st.error("❌ Não foi possível conectar ao banco de dados.")
        return
    try:
        funcao(conn)
    finally:
        conn.close()
    if st.button("🔙 Voltar ao menu"):
        st.session_state.pagina = "menu"

# Execução de páginas conforme a opção selecionada
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

elif st.session_state.pagina == "Cadastrar novo usuário":
    if st.session_state.usuario == SUPERUSUARIO:
        executar_pagina(cadastrar_usuario)
    else:
        st.error("Acesso negado.")

elif st.session_state.pagina == "Sair":
    st.session_state.clear()
    st.write("👋 Você saiu do sistema. Feche a aba do navegador para encerrar a sessão.")
    st.stop()
