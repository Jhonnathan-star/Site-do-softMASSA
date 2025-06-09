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

    # Adicionar nova falta
    st.markdown("### ➕ Registrar nova falta")
    nova_data = st.date_input("Data da falta", value=date.today(), key="falta_data")
    novo_motivo = st.text_input("Motivo", key="falta_motivo")

    if st.button("Registrar falta"):
        if novo_motivo:
            cursor.execute(
                "INSERT INTO faltas (id_usuario, data, motivo) VALUES (%s, %s, %s)",
                (id_usuario, nova_data, novo_motivo)
            )
            conn.commit()
            st.success("✅ Falta registrada com sucesso!")
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

            nova_data = st.date_input("Nova data", value=pd.to_datetime(falta["Data"]).date(), key="editar_falta_data")
            novo_motivo = st.text_input("Novo motivo", value=falta["Motivo"], key="editar_falta_motivo")

            col1, col2 = st.columns(2)
            if col1.button("Salvar alteração na falta"):
                cursor.execute(
                    "UPDATE faltas SET data = %s, motivo = %s WHERE id = %s",
                    (nova_data, novo_motivo, int(falta["ID"]))
                )
                conn.commit()
                st.success("✅ Falta atualizada com sucesso!")
                st.rerun()

            if col2.button("🗑️ Excluir esta falta"):
                cursor.execute("DELETE FROM faltas WHERE id = %s", (int(falta["ID"]),))
                conn.commit()
                st.warning("❌ Falta excluída com sucesso!")
                st.rerun()

    if st.button("🧨 Excluir todas as faltas deste funcionário"):
        cursor.execute("DELETE FROM faltas WHERE id_usuario = %s", (id_usuario,))
        conn.commit()
        st.warning("❌ Todas as faltas deste funcionário foram excluídas.")
        st.rerun()
