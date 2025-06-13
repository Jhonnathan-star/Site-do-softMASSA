import streamlit as st
import pandas as pd
from datetime import date

def visualizar_faltas(conn, id_usuario, nome_usuario, tipo_usuario):
    st.subheader(f"📋 Faltas de: **{nome_usuario}**")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, data, motivo FROM faltas WHERE id_usuario = %s ORDER BY data DESC",
        (id_usuario,)
    )
    faltas = cursor.fetchall()
    df = pd.DataFrame(faltas, columns=["ID", "Data", "Motivo"])

    if not df.empty:
        st.table(df.drop(columns=["ID"]))
    else:
        st.info("Nenhuma falta registrada.")

    if tipo_usuario != "admin":
        return

    # Inicializar valores no session_state se ainda não existirem
    if "falta_data" not in st.session_state:
        st.session_state["falta_data"] = date.today()
    if "falta_motivo" not in st.session_state:
        st.session_state["falta_motivo"] = ""

    # Adicionar nova falta
    st.markdown("### ➕ Registrar nova falta")
    nova_data = st.date_input("Data da falta", key="falta_data")
    novo_motivo = st.text_input("Motivo", key="falta_motivo")

    if st.button("Registrar falta"):
        if novo_motivo.strip():
            cursor.execute(
                "INSERT INTO faltas (id_usuario, data, motivo) VALUES (%s, %s, %s)",
                (id_usuario, nova_data, novo_motivo.strip())
            )
            conn.commit()
            st.success("✅ Falta registrada com sucesso!")

            # Resetar campos removendo as chaves antes do rerun
            del st.session_state["falta_data"]
            del st.session_state["falta_motivo"]
            st.rerun()
        else:
            st.warning("⚠️ Motivo não pode estar em branco.")

    # Editar ou excluir falta
    if not df.empty:
        st.markdown("### ✏️ Editar ou Excluir Falta")
        opcoes = [f"{row['Data']} - {row['Motivo']}" for _, row in df.iterrows()]
        falta_sel = st.selectbox("Selecione uma falta para editar:", ["Nenhuma"] + opcoes)

        if falta_sel != "Nenhuma":
            idx = opcoes.index(falta_sel)
            falta = df.iloc[idx]

            # Inicializar os valores de edição no session_state se não existirem
            if "editar_falta_data" not in st.session_state:
                st.session_state["editar_falta_data"] = pd.to_datetime(falta["Data"]).date()
            if "editar_falta_motivo" not in st.session_state:
                st.session_state["editar_falta_motivo"] = falta["Motivo"]

            nova_data = st.date_input("Nova data", key="editar_falta_data")
            novo_motivo = st.text_input("Novo motivo", key="editar_falta_motivo")

            col1, col2 = st.columns(2)
            if col1.button("Salvar alteração na falta"):
                cursor.execute(
                    "UPDATE faltas SET data = %s, motivo = %s WHERE id = %s",
                    (nova_data, novo_motivo.strip(), int(falta["ID"]))
                )
                conn.commit()
                st.success("✅ Falta atualizada com sucesso!")

                # Resetar os campos de edição para evitar conflito no próximo loop
                del st.session_state["editar_falta_data"]
                del st.session_state["editar_falta_motivo"]
                st.rerun()

            # Confirmação para excluir esta falta
            if "confirmar_excluir_falta" not in st.session_state:
                st.session_state.confirmar_excluir_falta = False

            if not st.session_state.confirmar_excluir_falta:
                if col2.button("🗑️ Excluir esta falta"):
                    st.session_state.id_falta_excluir = int(falta["ID"])
                    st.session_state.confirmar_excluir_falta = True

            if st.session_state.confirmar_excluir_falta:
                st.warning("⚠️ Deseja realmente excluir esta falta?")
                col3, col4 = st.columns(2)
                if col3.button("✅ Sim, excluir falta"):
                    cursor.execute("DELETE FROM faltas WHERE id = %s", (st.session_state.id_falta_excluir,))
                    conn.commit()
                    st.session_state.confirmar_excluir_falta = False
                    st.success("❌ Falta excluída com sucesso!")
                    st.experimental_rerun()
                if col4.button("❌ Não, cancelar exclusão"):
                    st.session_state.confirmar_excluir_falta = False
                    st.rerun()

    # Confirmação para excluir todas as faltas
    if "confirmar_excluir_todas" not in st.session_state:
        st.session_state.confirmar_excluir_todas = False

    st.markdown("---")
    if not st.session_state.confirmar_excluir_todas:
        if st.button("🧨 Excluir todas as faltas deste funcionário"):
            st.session_state.confirmar_excluir_todas = True

    if st.session_state.confirmar_excluir_todas:
        st.warning("⚠️ Deseja realmente excluir todas as faltas deste funcionário?")
        col5, col6 = st.columns(2)
        if col5.button("✅ Sim, excluir todas"):
            cursor.execute("DELETE FROM faltas WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            st.session_state.confirmar_excluir_todas = False
            st.warning("❌ Todas as faltas foram excluídas.")
            st.rerun()
        if col6.button("❌ Não, cancelar"):
            st.session_state.confirmar_excluir_todas = False
            st.rerun()
