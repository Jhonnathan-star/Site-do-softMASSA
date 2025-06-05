import streamlit as st
from datetime import datetime, timedelta
from utils.calculos import calcular_pacotes

def inserir_pedidos_automatizado(conn):
    cursor = conn.cursor(dictionary=True)

    st.header("Inserir Pedidos Automatizados")

    tipo_pao_grossa = st.selectbox("Qual tipo de grossa?", options=["G3", "G4"])
    tipo_pao_fina = st.selectbox("Qual tipo de fina?", options=["F3", "F4"])

    data_inicio = st.date_input("Data início")
    data_fim = st.date_input("Data fim")

    # Botão para calcular a previsão
    if st.button("Calcular previsão"):
        if data_fim < data_inicio:
            st.error("Data fim deve ser maior ou igual à data início.")
            return

        dias = (data_fim - data_inicio).days + 1
        resultados = []
        total_grossa = 0
        total_fina = 0

        for i in range(dias):
            data_atual = data_inicio + timedelta(days=i)
            query = """
                SELECT telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde
                FROM telas
                WHERE data = %s
            """
            cursor.execute(query, (str(data_atual),))
            resultado = cursor.fetchone()

            if resultado:
                telas_grossa_manha = resultado['telas_grossa_manha'] or 0
                telas_grossa_tarde = resultado['telas_grossa_tarde'] or 0
                telas_fina_manha = resultado['telas_fina_manha'] or 0
                telas_fina_tarde = resultado['telas_fina_tarde'] or 0

                pacotes_grossa = calcular_pacotes(telas_grossa_manha, tipo_pao_grossa) + calcular_pacotes(telas_grossa_tarde, tipo_pao_grossa)
                pacotes_fina = calcular_pacotes(telas_fina_manha, tipo_pao_fina) + calcular_pacotes(telas_fina_tarde, tipo_pao_fina)
            else:
                pacotes_grossa = 0
                pacotes_fina = 0

            resultados.append((data_atual, pacotes_grossa, pacotes_fina))
            total_grossa += pacotes_grossa
            total_fina += pacotes_fina

        valor_total = (total_grossa + total_fina) * 62 # Valor do pct

        # Armazena no session_state para persistência
        st.session_state['resultados'] = resultados
        st.session_state['total_grossa'] = total_grossa
        st.session_state['total_fina'] = total_fina
        st.session_state['valor_total'] = valor_total
        st.session_state['data_inicio'] = data_inicio
        st.session_state['tipo_pao_grossa'] = tipo_pao_grossa
        st.session_state['tipo_pao_fina'] = tipo_pao_fina

    # Mostrar resultados se já calculados
    if 'resultados' in st.session_state:
        st.subheader("Previsão por dia")
        st.write("---")
        for data_atual, pct_grossa, pct_fina in st.session_state['resultados']:
            st.write(f"{data_atual}: Grossa: {pct_grossa} pct | Fina: {pct_fina} pct")

        st.write("---")
        st.write(f"**Total de pacotes de {st.session_state['tipo_pao_grossa']} (grossa):** {st.session_state['total_grossa']} pct")
        st.write(f"**Total de pacotes de {st.session_state['tipo_pao_fina']} (fina):** {st.session_state['total_fina']} pct")
        st.write(f"**Valor total estimado:** R$ {st.session_state['valor_total']:.2f}")

        inserir = st.radio("Deseja inserir esses dados na tabela 'pedidos'?", ("Não", "Sim"))

        if inserir == "Sim":
            insert_query = """
                INSERT INTO pedidos (`Data`, `Grossa (PCT)`, `Fina (PCT)`, `Valor R$`)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                str(st.session_state['data_inicio']),
                st.session_state['total_grossa'],
                st.session_state['total_fina'],
                st.session_state['valor_total']
            ))
            conn.commit()
            st.success(f"Dados inseridos na tabela 'pedidos'. Valor total: R$ {st.session_state['valor_total']:.2f}")

            # Limpa o session_state para evitar múltiplas inserções acidentais
            for key in ['resultados', 'total_grossa', 'total_fina', 'valor_total', 'data_inicio', 'tipo_pao_grossa', 'tipo_pao_fina']:
                del st.session_state[key]

    cursor.close()

import streamlit as st
from datetime import datetime, timedelta
from utils.calculos import calcular_pacotes

import streamlit as st
from datetime import datetime, timedelta
from utils.calculos import calcular_pacotes  # Certifique-se que está importado

import streamlit as st
from datetime import timedelta

def inserir_pedidos_manual(conn):
    cursor = conn.cursor()

    st.header("Inserir previsão manual de pedidos")

    data = st.date_input("Data da previsão")

    tipo_pao_grossa = st.selectbox("Qual tipo de grossa?", options=["G3", "G4"])
    tipo_pao_fina = st.selectbox("Qual tipo de fina?", options=["F3", "F4"])

    qtde_telas_grossa = st.number_input(f"Quantas telas de Grossa {tipo_pao_grossa}?", min_value=0, step=1)
    qtde_telas_fina = st.number_input(f"Quantas telas de Fina {tipo_pao_fina}?", min_value=0, step=1)

    if st.button("Calcular previsão e mostrar resultados"):
        pacotes_grossa = calcular_pacotes(qtde_telas_grossa, tipo_pao_grossa)
        pacotes_fina = calcular_pacotes(qtde_telas_fina, tipo_pao_fina)

        dias = [data, data + timedelta(days=1)]
        pacotes_g_por_dia = pacotes_grossa // 2
        pacotes_f_por_dia = pacotes_fina // 2

        st.subheader("Previsão por dia")
        for dia in dias:
            st.write(f"{dia}: Grossa: {pacotes_g_por_dia} pct | Fina: {pacotes_f_por_dia} pct")

        st.write("---")
        st.write(f"**Total de pacotes de {tipo_pao_grossa} (grossa):** {pacotes_grossa} pct")
        st.write(f"**Total de pacotes de {tipo_pao_fina} (fina):** {pacotes_fina} pct")

        valor_total = (pacotes_grossa + pacotes_fina) * 62 # Valor do pct de massa
        st.write(f"**Valor total estimado:** R$ {valor_total:.2f}")

        # Guardar o valor para inserção em session_state para persistir
        st.session_state['inserir_valores'] = {
            "data": str(data),
            "pacotes_grossa": pacotes_grossa,
            "pacotes_fina": pacotes_fina,
            "valor_total": valor_total
        }

    if 'inserir_valores' in st.session_state:
        inserir = st.radio("Deseja inserir esses dados na tabela 'pedidos'?", ("Não", "Sim"), key="inserir_radio")
        if inserir == "Sim":
            try:
                vals = st.session_state['inserir_valores']
                insert_query = """
                    INSERT INTO pedidos (`Data`, `Grossa (PCT)`, `Fina (PCT)`, `Valor R$`)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (vals["data"], vals["pacotes_grossa"], vals["pacotes_fina"], vals["valor_total"]))
                conn.commit()
                st.success(f"Dados inseridos na tabela 'pedidos'. Valor total: R$ {vals['valor_total']:.2f}")
                # Limpar sessão para evitar reinserção
                del st.session_state['inserir_valores']
            except Exception as e:
                st.error(f"Erro ao inserir no banco: {e}")

    cursor.close()

