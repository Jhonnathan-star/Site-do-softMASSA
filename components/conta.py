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

    # Edição e exclusão
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

            if col2.button("🗑️ Excluir este item"):
                cursor.execute("DELETE FROM conta_funcionarios WHERE id = %s", (int(item["ID"]),))
                conn.commit()
                st.warning("❌ Item excluído com sucesso!")
                st.rerun()

    # Adicionar gasto
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
                (id_usuario, novo_valor, nova_desc, nova_data)
            )
            conn.commit()
            st.success("✅ Gasto adicionado com sucesso!")
            st.rerun()
        else:
            st.warning("⚠️ Preencha todos os campos obrigatórios.")

    if st.button("🧨 Excluir todos os registros desta conta"):
        cursor.execute("DELETE FROM conta_funcionarios WHERE id_usuario = %s", (id_usuario,))
        conn.commit()
        st.warning("❌ Todos os registros desta conta foram excluídos.")
        st.rerun()
