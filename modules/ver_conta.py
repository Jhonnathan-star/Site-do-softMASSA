import streamlit as st
import pandas as pd
from datetime import date
from database.connection import conectar

def login(conn):
    st.subheader("🔐 Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, superusuario FROM usuarios WHERE usuario = %s AND senha = %s",
            (usuario, senha)
        )
        resultado = cursor.fetchone()

        if resultado:
            st.session_state["id_usuario"] = resultado[0]
            st.session_state["superusuario"] = resultado[1]
            st.session_state["usuario"] = usuario
            st.success(f"✅ Logado como {usuario}")
            st.rerun()
        else:
            st.error("❌ Usuário ou senha inválidos")

def ver_conta_funcionario(conn):
    st.subheader("💰 Ver Conta de Funcionário")
    cursor = conn.cursor()

    cursor.execute("SELECT id, usuario FROM usuarios ORDER BY usuario")
    usuarios = cursor.fetchall()

    if not usuarios:
        st.warning("Nenhum usuário encontrado.")
        return

    nomes_usuarios = [u[1] for u in usuarios]
    nome_selecionado = st.selectbox("Selecione o funcionário:", nomes_usuarios)
    id_usuario_selecionado = next(u[0] for u in usuarios if u[1] == nome_selecionado)

    cursor.execute(
        "SELECT id, valor, descricao, data FROM conta_funcionarios WHERE id_usuario = %s ORDER BY data",
        (id_usuario_selecionado,)
    )
    registros = cursor.fetchall()

    if registros:
        df = pd.DataFrame(registros, columns=["ID", "Valor (R$)", "Descrição", "Data"])
        st.write(f"📄 Conta de: **{nome_selecionado}**")
        st.table(df.drop(columns=["ID"]))

        total = df["Valor (R$)"].sum()
        st.success(f"💵 Total: R$ {total:.2f}")
    else:
        st.info("Nenhum registro de conta encontrado.")

    superusuario = st.session_state.get("superusuario", False)

    if superusuario:
        st.markdown("---")
        st.subheader("✏️ Editar ou Excluir Gasto")

        if registros:
            opcoes_linhas = [
                f"{row['Descrição']} - R$ {row['Valor (R$)']:.2f} - {row['Data']}"
                for _, row in df.iterrows()
            ]
            editar_idx = st.selectbox("Selecione um registro:", ["Nenhuma"] + opcoes_linhas)

            if editar_idx != "Nenhuma":
                index = opcoes_linhas.index(editar_idx)
                item = df.iloc[index]

                valor_str = st.text_input("Novo valor (R$)", value=f"{item['Valor (R$)']:.2f}")
                try:
                    novo_valor = float(valor_str.replace(",", "."))
                except ValueError:
                    novo_valor = None

                nova_desc = st.text_input("Nova descrição", value=item["Descrição"])
                nova_data = st.date_input("Nova data", value=pd.to_datetime(item["Data"]).date())

                col1, col2 = st.columns(2)
                if col1.button("Salvar alterações"):
                    if novo_valor is not None:
                        cursor.execute(
                            "UPDATE conta_funcionarios SET valor = %s, descricao = %s, data = %s WHERE id = %s",
                            (novo_valor, nova_desc, nova_data, int(item["ID"]))
                        )
                        conn.commit()
                        st.success("✅ Alterações salvas com sucesso!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Valor inválido.")

                if col2.button("🗑️ Excluir este item"):
                    cursor.execute("DELETE FROM conta_funcionarios WHERE id = %s", (int(item["ID"]),))
                    conn.commit()
                    st.warning("❌ Item excluído com sucesso!")
                    st.rerun()

        st.markdown("---")
        st.subheader("➕ Adicionar novo gasto")

        valor_str = st.text_input("Valor (R$)")
        try:
            novo_valor = float(valor_str.replace(",", "."))
        except ValueError:
            novo_valor = None

        nova_desc = st.text_input("Descrição")
        nova_data = st.date_input("Data", value=date.today())

        if st.button("Adicionar gasto"):
            if nova_desc and novo_valor is not None:
                cursor.execute(
                    "INSERT INTO conta_funcionarios (id_usuario, valor, descricao, data) VALUES (%s, %s, %s, %s)",
                    (id_usuario_selecionado, novo_valor, nova_desc, nova_data)
                )
                conn.commit()
                st.success("✅ Gasto adicionado com sucesso!")
                st.rerun()
            else:
                st.warning("⚠️ Preencha todos os campos obrigatórios.")

        if st.button("🧨 Excluir todos os registros desta conta"):
            cursor.execute("DELETE FROM conta_funcionarios WHERE id_usuario = %s", (id_usuario_selecionado,))
            conn.commit()
            st.warning("❌ Todos os registros desta conta foram excluídos.")
            st.rerun()

def main():
    st.set_page_config(page_title="Conta de Funcionários", layout="centered")
    conn = conectar()

    if "id_usuario" not in st.session_state:
        login(conn)
    else:
        st.sidebar.write(f"👤 Logado como: **{st.session_state.get('usuario')}**")
        if st.sidebar.button("🚪 Sair"):
            for key in ["id_usuario", "superusuario", "usuario"]:
                st.session_state.pop(key, None)
            st.rerun()

        ver_conta_funcionario(conn)

    conn.close()

if __name__ == "__main__":
    main()
