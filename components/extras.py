import streamlit as st
import pandas as pd
from datetime import date

def visualizar_extras(conn, id_usuario, nome_usuario, tipo_usuario):
    st.subheader(f"📌 Extras de: **{nome_usuario}**")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, data, turno FROM extras WHERE id_usuario = %s ORDER BY data DESC",
        (id_usuario,)
    )
    extras = cursor.fetchall()
    df = pd.DataFrame(extras, columns=["ID", "Data", "Turno"])

    if not df.empty:
        st.table(df.drop(columns=["ID"]))
    else:
        st.info("Nenhum extra registrado.")

    if tipo_usuario != "admin":
        return

    # Inicializar valores no session_state se ainda não existirem
    if "extra_data" not in st.session_state:
        st.session_state["extra_data"] = date.today()
    if "extra_turno" not in st.session_state:
        st.session_state["extra_turno"] = "manhã"

    # Adicionar novo extra
    st.markdown("### ➕ Registrar novo extra")
    nova_data = st.date_input("Data do extra", key="extra_data")
    novo_turno = st.radio("Turno", ["manhã", "tarde", "Dia todo"], key="extra_turno")

    if st.button("Registrar extra"):
        cursor.execute(
            "INSERT INTO extras (id_usuario, data, turno) VALUES (%s, %s, %s)",
            (id_usuario, nova_data, novo_turno)
        )
        conn.commit()
        st.success("✅ Extra registrado com sucesso!")

        del st.session_state["extra_data"]
        del st.session_state["extra_turno"]
        st.rerun()

    # Editar ou excluir extra
    if not df.empty:
        st.markdown("### ✏️ Editar ou Excluir Extra")
        opcoes = [f"{row['Data']} - {row['Turno']}" for _, row in df.iterrows()]
        extra_sel = st.selectbox("Selecione um extra para editar:", ["Nenhuma"] + opcoes)

        if extra_sel != "Nenhuma":
            idx = opcoes.index(extra_sel)
            extra = df.iloc[idx]

            # Inicializar valores de edição no session_state
            if "editar_extra_data" not in st.session_state:
                st.session_state["editar_extra_data"] = pd.to_datetime(extra["Data"]).date()
            if "editar_extra_turno" not in st.session_state:
                st.session_state["editar_extra_turno"] = extra["Turno"]

            nova_data = st.date_input("Nova data", key="editar_extra_data")
            novo_turno = st.radio("Novo turno", ["manhã", "tarde", "dia todo"], key="editar_extra_turno")

            col1, col2 = st.columns(2)
            if col1.button("Salvar alterações"):
                cursor.execute(
                    "UPDATE extras SET data = %s, turno = %s WHERE id = %s",
                    (nova_data, novo_turno, int(extra["ID"]))
                )
                conn.commit()
                st.success("✅ Extra atualizado com sucesso!")
                del st.session_state["editar_extra_data"]
                del st.session_state["editar_extra_turno"]
                st.rerun()

            # Confirmação para excluir este extra
            if "confirmar_excluir_extra" not in st.session_state:
                st.session_state.confirmar_excluir_extra = False

            if not st.session_state.confirmar_excluir_extra:
                if col2.button("🗑️ Excluir este extra"):
                    st.session_state.id_extra_excluir = int(extra["ID"])
                    st.session_state.confirmar_excluir_extra = True

            if st.session_state.confirmar_excluir_extra:
                st.warning("⚠️ Deseja realmente excluir este extra?")
                col3, col4 = st.columns(2)
                if col3.button("✅ Sim, excluir"):
                    cursor.execute("DELETE FROM extras WHERE id = %s", (st.session_state.id_extra_excluir,))
                    conn.commit()
                    st.session_state.confirmar_excluir_extra = False
                    st.success("❌ Extra excluído com sucesso!")
                    st.rerun()
                if col4.button("❌ Não, cancelar"):
                    st.session_state.confirmar_excluir_extra = False
                    st.rerun()

    # Excluir todos os extras
    if "confirmar_excluir_todos_extras" not in st.session_state:
        st.session_state.confirmar_excluir_todos_extras = False

    st.markdown("---")
    if not st.session_state.confirmar_excluir_todos_extras:
        if st.button("🧨 Excluir todos os extras deste funcionário"):
            st.session_state.confirmar_excluir_todos_extras = True

    if st.session_state.confirmar_excluir_todos_extras:
        st.warning("⚠️ Deseja realmente excluir todos os extras deste funcionário?")
        col5, col6 = st.columns(2)
        if col5.button("✅ Sim, excluir todos"):
            cursor.execute("DELETE FROM extras WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            st.session_state.confirmar_excluir_todos_extras = False
            st.warning("❌ Todos os extras foram excluídos.")
            st.rerun()
        if col6.button("❌ Não, cancelar"):
            st.session_state.confirmar_excluir_todos_extras = False
            st.rerun()
