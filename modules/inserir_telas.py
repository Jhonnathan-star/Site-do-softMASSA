import streamlit as st

def inserir_telas(conn):
    st.subheader("📅 Inserir dados de telas")

    # Data e dia da semana
    data = st.date_input("Selecione a data", format="YYYY-MM-DD")
    semana = data.strftime("%A")
    domingo = semana == "Sunday"
    semana_pt = data.strftime("%A").capitalize()

    st.write(f"🗓️ Dia selecionado: **{semana_pt}**")

    # Telas grossa - manhã
    telas_grossa_manha = st.number_input("📌 **Telas grossa - manhã**", min_value=0, step=1)

    # Telas grossa - tarde (somente se não for domingo)
    if not domingo:
        telas_grossa_tarde = st.number_input("📌 **Telas grossa - tarde**", min_value=0, step=1)
    else:
        telas_grossa_tarde = 0

    # Telas fina - manhã
    telas_fina_manha = st.number_input("📌 **Telas fina - manhã**", min_value=0, step=1)

    # Telas fina - tarde (somente se não for domingo)
    if not domingo:
        telas_fina_tarde = st.number_input("📌 **Telas fina - tarde**", min_value=0, step=1)
    else:
        telas_fina_tarde = 0
        st.info("É domingo. Campos da tarde serão registrados como 0 automaticamente.")

    # Botão de inserção com verificação de duplicatas
    if st.button("Inserir dados de telas"):
        try:
            cursor = conn.cursor()

            # Verifica se já existe dado na mesma data
            cursor.execute("SELECT COUNT(*) FROM telas WHERE data = %s", (data.strftime("%Y-%m-%d"),))
            resultado = cursor.fetchone()

            if resultado[0] > 0:
                st.warning(f"⚠️ Já existem dados inseridos para o dia {data.strftime('%Y-%m-%d')}.")
            else:
                sql = """
                    INSERT INTO telas (
                        data, semana,
                        telas_grossa_manha, telas_grossa_tarde,
                        telas_fina_manha, telas_fina_tarde
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                valores = (
                    data.strftime("%Y-%m-%d"),
                    semana,
                    telas_grossa_manha, telas_grossa_tarde,
                    telas_fina_manha, telas_fina_tarde
                )
                cursor.execute(sql, valores)
                conn.commit()

                st.success(f"✅ Dados inseridos com sucesso para {semana_pt} ({data.strftime('%Y-%m-%d')})")

        except Exception as e:
            st.error(f"❌ Erro ao inserir dados: {e}")
