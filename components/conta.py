import streamlit as st
import pandas as pd
from datetime import date

def visualizar_contas(conn, id_usuario, nome_usuario, tipo_usuario):
    st.subheader(f"📄 Conta de: **{nome_usuario}**")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, valor, descricao, data FROM conta_funcionarios WHERE id_usuario = %s ORDER BY data",
        (id_usuario,)
    )
    registros = cursor.fetchall()

    if registros:
        df = pd.DataFrame(registros, columns=["ID", "Valor (R$)", "Descrição", "Data"])
        st.table(df.drop(columns=["ID"]))
        total = df["Valor (R$)"].sum()
        st.success(f"💵 Total: R$ {total:.2f}")
    else:
        st.info("Nenhum registro de conta encontrado.")
        df = pd.DataFrame()

    if tipo_usuario != "admin":
        return

    st.markdown("---")
    st.subheader("✏️ Editar ou Excluir Gasto")

    if not df.empty:
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

            # Confirmação de exclusão individual
            if "confirmar_exclusao_item" not in st.session_state:
                st.session_state.confirmar_exclusao_item = False

            if not st.session_state.confirmar_exclusao_item:
                if col2.button("🗑️ Excluir este item"):
                    st.session_state.id_exclusao_item = int(item["ID"])
                    st.session_state.confirmar_exclusao_item = True

            if st.session_state.confirmar_exclusao_item:
                st.warning("⚠️ Tem certeza que deseja excluir este item?")
                col3, col4 = st.columns(2)
                if col3.button("✅ Sim, excluir"):
                    cursor.execute("DELETE FROM conta_funcionarios WHERE id = %s", (st.session_state.id_exclusao_item,))
                    conn.commit()
                    st.session_state.confirmar_exclusao_item = False
                    st.success("❌ Item excluído com sucesso!")
                    st.rerun()
                if col4.button("❌ Não, cancelar"):
                    st.session_state.confirmar_exclusao_item = False
                    st.rerun()

    # -----------------------------
    # Adicionar novo gasto
    # -----------------------------

    st.markdown("---")
    st.subheader("➕ Adicionar novo gasto")

    # Inicializar valores no session_state para evitar warning
    if st.session_state.get("limpar_campos_gasto", False):
        st.session_state["limpar_campos_gasto"] = False
        st.session_state["novo_gasto_valor"] = ""
        st.session_state["novo_gasto_desc"] = ""
        st.session_state["novo_gasto_data"] = date.today()

    if "novo_gasto_data" not in st.session_state:
        st.session_state["novo_gasto_data"] = date.today()
    if "novo_gasto_valor" not in st.session_state:
        st.session_state["novo_gasto_valor"] = ""
    if "novo_gasto_desc" not in st.session_state:
        st.session_state["novo_gasto_desc"] = ""

    valor_str = st.text_input("Valor (R$)", key="novo_gasto_valor")
    nova_desc = st.text_input("Descrição", key="novo_gasto_desc")
    nova_data = st.date_input("Data", key="novo_gasto_data")

    try:
        novo_valor = float(valor_str.replace(",", "."))
    except ValueError:
        novo_valor = None

    if st.button("Adicionar gasto"):
        if nova_desc and novo_valor is not None:
            cursor.execute(
                "INSERT INTO conta_funcionarios (id_usuario, valor, descricao, data) VALUES (%s, %s, %s, %s)",
                (id_usuario, novo_valor, nova_desc, nova_data)
            )
            conn.commit()
            st.success("✅ Gasto adicionado com sucesso!")
            st.session_state["limpar_campos_gasto"] = True
            st.rerun()
        else:
            st.warning("⚠️ Preencha todos os campos obrigatórios.")

    # -----------------------------
    # Confirmação para excluir todos os registros
    # -----------------------------
    if "confirmar_exclusao" not in st.session_state:
        st.session_state.confirmar_exclusao = False

    st.markdown("---")
    if not st.session_state.confirmar_exclusao:
        if st.button("🧨 Excluir todos os registros desta conta"):
            st.session_state.confirmar_exclusao = True

    if st.session_state.confirmar_exclusao:
        st.markdown(
            """
            <div style='background-color:#ffe6e6; padding:20px; border-radius:10px; border: 2px solid red;'>
                <h4 style='color:#b30000;'>⚠️ Deseja realmente excluir <u>todos os registros</u> desta conta?</h4>
                <p style='margin-bottom:10px;'>Esta ação não pode ser desfeita.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col5, col6 = st.columns(2)
        if col5.button("✅ Sim, excluir tudo"):
            cursor.execute("DELETE FROM conta_funcionarios WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            st.session_state.confirmar_exclusao = False
            st.warning("❌ Todos os registros desta conta foram excluídos.")
            st.rerun()

        if col6.button("❌ Não, cancelar"):
            st.session_state.confirmar_exclusao = False
            st.rerun()
