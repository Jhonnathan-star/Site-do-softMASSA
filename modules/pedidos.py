import streamlit as st
from datetime import datetime, timedelta
from utils.calculos import calcular_pacotes

def inserir_pedidos_automatizado(conn):
    cursor = conn.cursor(dictionary=True)

    st.header("Inserir Pedidos Automatizados")

    valor_pacote = st.number_input("Valor do pacote (R$)", min_value=0.0, step=1.0, value=62.0)

    tipo_pao_grossa = st.selectbox("Qual tipo de grossa?", options=["G3", "G4"])
    tipo_pao_fina = st.selectbox("Qual tipo de fina?", options=["F3", "F4"])

    data_inicio = st.date_input("Data início")
    turno_inicio = st.selectbox("Turno início", options=["manhã", "tarde"])

    data_fim = st.date_input("Data fim")
    turno_fim = st.selectbox("Turno fim", options=["manhã", "tarde"])

    if st.button("Calcular previsão"):
        if (data_fim < data_inicio) or (data_fim == data_inicio and turno_fim == "manhã" and turno_inicio == "tarde"):
            st.error("Data/turno fim deve ser maior ou igual à data/turno início.")
            return

        resultados = []
        total_grossa = 0
        total_fina = 0

        data_atual = data_inicio
        turno_atual = turno_inicio

        while True:
            query = """
                SELECT telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde
                FROM telas
                WHERE data = %s
            """
            cursor.execute(query, (str(data_atual),))
            resultado = cursor.fetchone()

            if resultado:
                g_manha = resultado['telas_grossa_manha'] or 0
                g_tarde = resultado['telas_grossa_tarde'] or 0
                f_manha = resultado['telas_fina_manha'] or 0
                f_tarde = resultado['telas_fina_tarde'] or 0
            else:
                g_manha = g_tarde = f_manha = f_tarde = 0

            pacotes_grossa = 0
            pacotes_fina = 0

            if turno_atual == "manhã":
                pacotes_grossa = calcular_pacotes(g_manha, tipo_pao_grossa)
                pacotes_fina = calcular_pacotes(f_manha, tipo_pao_fina)
            elif turno_atual == "tarde":
                pacotes_grossa = calcular_pacotes(g_tarde, tipo_pao_grossa)
                pacotes_fina = calcular_pacotes(f_tarde, tipo_pao_fina)

            resultados.append((data_atual, turno_atual, pacotes_grossa, pacotes_fina))
            total_grossa += pacotes_grossa
            total_fina += pacotes_fina

            if data_atual == data_fim and turno_atual == turno_fim:
                break

            if turno_atual == "manhã":
                turno_atual = "tarde"
            else:
                turno_atual = "manhã"
                data_atual += timedelta(days=1)

        valor_total = (total_grossa + total_fina) * valor_pacote

        # Guardar no session_state para mostrar e inserir
        st.session_state['resultados'] = resultados
        st.session_state['total_grossa'] = total_grossa
        st.session_state['total_fina'] = total_fina
        st.session_state['valor_total'] = valor_total
        st.session_state['data_inicio'] = data_inicio
        st.session_state['tipo_pao_grossa'] = tipo_pao_grossa
        st.session_state['tipo_pao_fina'] = tipo_pao_fina
        st.session_state['valor_pacote'] = valor_pacote

    if 'resultados' in st.session_state:
        st.subheader("Previsão por dia e turno")
        st.write("---")
        for data_, turno_, pct_grossa, pct_fina in st.session_state['resultados']:
            st.write(f"{data_} - {turno_}: Grossa: {pct_grossa} pct | Fina: {pct_fina} pct")

        st.write("---")
        st.markdown("### Editar previsão total de pacotes")

        total_grossa_editado = st.number_input(
            f"Editar total de pacotes GROSSA ({st.session_state.get('tipo_pao_grossa', 'G3')})",
            value=st.session_state.get('total_grossa', 0),
            min_value=0,
            step=1,
            key="input_total_grossa"
        )

        total_fina_editado = st.number_input(
            f"Editar total de pacotes FINA ({st.session_state.get('tipo_pao_fina', 'F3')})",
            value=st.session_state.get('total_fina', 0),
            min_value=0,
            step=1,
            key="input_total_fina"
        )

        if st.button("Recalcular valor total"):
            novo_valor_total = (total_grossa_editado + total_fina_editado) * st.session_state.get('valor_pacote', 62.0)
            st.session_state['valor_total_editado'] = novo_valor_total
            st.session_state['pacotes_grossa_editado'] = total_grossa_editado
            st.session_state['pacotes_fina_editado'] = total_fina_editado

        if 'valor_total_editado' in st.session_state:
            st.write(f"**Novo valor total estimado:** R$ {st.session_state['valor_total_editado']:.2f}")

            inserir = st.radio("Deseja inserir esses dados na tabela 'pedidos'?", ("Não", "Sim"))

            if inserir == "Sim":
                insert_query = """
                    INSERT INTO pedidos (Data, `Grossa (PCT)`, `Fina (PCT)`, `Valor R$`)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    str(st.session_state.get('data_inicio')),
                    st.session_state['pacotes_grossa_editado'],
                    st.session_state['pacotes_fina_editado'],
                    st.session_state['valor_total_editado']
                ))
                conn.commit()
                st.success(f"Dados inseridos na tabela 'pedidos'. Valor total: R$ {st.session_state['valor_total_editado']:.2f}")

                # Limpar sessão
                for key in ['resultados', 'total_grossa', 'total_fina', 'valor_total',
                            'data_inicio', 'tipo_pao_grossa', 'tipo_pao_fina',
                            'valor_pacote', 'valor_total_editado',
                            'pacotes_grossa_editado', 'pacotes_fina_editado']:
                    if key in st.session_state:
                        del st.session_state[key]

    cursor.close()

def inserir_pedidos_manual(conn):
    cursor = conn.cursor()

    st.header("Inserir previsão manual de pedidos")

    valor_pacote = st.number_input("Valor do pacote (R$)", min_value=0.0, step=1.0, value=62.0)

    data = st.date_input("Data da previsão")

    tipo_pao_grossa = st.selectbox("Qual tipo de grossa?", options=["G3", "G4"])
    tipo_pao_fina = st.selectbox("Qual tipo de fina?", options=["F3", "F4"])

    qtde_telas_grossa = st.number_input(f"Quantas telas de Grossa {tipo_pao_grossa}?", min_value=0, step=1, key="qtde_grossa_manual")
    qtde_telas_fina = st.number_input(f"Quantas telas de Fina {tipo_pao_fina}?", min_value=0, step=1, key="qtde_fina_manual")

    if st.button("Calcular previsão e mostrar resultados", key="calcular_manual"):
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

        valor_total = (pacotes_grossa + pacotes_fina) * valor_pacote
        st.write(f"**Valor total estimado:** R$ {valor_total:.2f}")

        # Salva no session_state para edição posterior
        st.session_state['resultados_manual'] = {
            "pacotes_grossa": pacotes_grossa,
            "pacotes_fina": pacotes_fina,
            "valor_total": valor_total,
            "valor_pacote": valor_pacote,
            "data": str(data),
            "tipo_pao_grossa": tipo_pao_grossa,
            "tipo_pao_fina": tipo_pao_fina
        }

    if 'resultados_manual' in st.session_state:
        st.markdown("### Editar previsão total de pacotes")

        total_grossa_editado = st.number_input(
            f"Editar total de pacotes GROSSA ({st.session_state['resultados_manual']['tipo_pao_grossa']})",
            value=st.session_state['resultados_manual']['pacotes_grossa'],
            min_value=0,
            step=1,
            key="input_total_grossa_manual"
        )

        total_fina_editado = st.number_input(
            f"Editar total de pacotes FINA ({st.session_state['resultados_manual']['tipo_pao_fina']})",
            value=st.session_state['resultados_manual']['pacotes_fina'],
            min_value=0,
            step=1,
            key="input_total_fina_manual"
        )

        if st.button("Recalcular valor total", key="recalcular_manual"):
            novo_valor_total = (total_grossa_editado + total_fina_editado) * st.session_state['resultados_manual']['valor_pacote']
            st.session_state['resultados_manual']['valor_total_editado'] = novo_valor_total
            st.session_state['resultados_manual']['pacotes_grossa_editado'] = total_grossa_editado
            st.session_state['resultados_manual']['pacotes_fina_editado'] = total_fina_editado

        if 'valor_total_editado' in st.session_state['resultados_manual']:
            st.write(f"**Novo valor total estimado:** R$ {st.session_state['resultados_manual']['valor_total_editado']:.2f}")

            inserir = st.radio("Deseja inserir esses dados na tabela 'pedidos'?", ("Não", "Sim"), key="inserir_radio_manual")
            if inserir == "Sim":
                try:
                    vals = st.session_state['resultados_manual']
                    insert_query = """
                        INSERT INTO pedidos (Data, `Grossa (PCT)`, `Fina (PCT)`, `Valor R$`)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        vals["data"],
                        vals.get('pacotes_grossa_editado', vals['pacotes_grossa']),
                        vals.get('pacotes_fina_editado', vals['pacotes_fina']),
                        vals['valor_total_editado']
                    ))
                    conn.commit()
                    st.success(f"Dados inseridos na tabela 'pedidos'. Valor total: R$ {vals['valor_total_editado']:.2f}")

                    # Limpar sessão após inserção
                    del st.session_state['resultados_manual']
                except Exception as e:
                    st.error(f"Erro ao inserir no banco: {e}")

    cursor.close()

def pagina_previsao_pedidos(conn):
    st.markdown("<h2 style='font-weight:bold; font-size:28px;'>Escolha o modo de previsão:</h2>", unsafe_allow_html=True)

    if 'modo_previsao' not in st.session_state:
        st.session_state['modo_previsao'] = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Manual"):
            st.session_state['modo_previsao'] = "manual"
            st.rerun()
    with col2:
        if st.button("Automática"):
            st.session_state['modo_previsao'] = "automatica"
            st.rerun()

    if st.session_state['modo_previsao'] == "manual":
        st.write("---")
        st.markdown("### Previsão Manual")
        inserir_pedidos_manual(conn)
        if st.button("Voltar à escolha"):
            st.session_state['modo_previsao'] = None
            st.rerun()

    elif st.session_state['modo_previsao'] == "automatica":
        st.write("---")
        st.markdown("### Previsão Automática")
        inserir_pedidos_automatizado(conn)
        if st.button("Voltar à escolha"):
            st.session_state['modo_previsao'] = None
            st.rerun()
