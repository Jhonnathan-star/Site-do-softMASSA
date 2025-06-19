import streamlit as st
from mysql.connector import Error
from database.connection import conectar

def get_conn():
    return conectar(st.session_state.get("banco_config"))

def cadastrar_ingrediente():
    st.subheader("Cadastrar Ingrediente")
    with st.form("form_ingrediente", clear_on_submit=True):
        nome = st.text_input("Nome do ingrediente")
        custo_unitario = st.number_input("Custo unitário", step=0.01, value=None, placeholder="Ex: 4.50")
        unidade = st.text_input("Unidade (ex: kg, litro, un)")
        submit = st.form_submit_button("Cadastrar ingrediente")

        if submit:
            if not nome or custo_unitario is None or custo_unitario <= 0 or not unidade:
                st.warning("Preencha todos os campos corretamente.")
                return

            conn = get_conn()
            if not conn:
                st.error("Erro ao conectar ao banco de dados.")
                return
            try:
                cursor = conn.cursor()
                sql = "INSERT INTO ingredientes (nome, custo_unitario, unidade_medida) VALUES (%s, %s, %s)"
                cursor.execute(sql, (nome, custo_unitario, unidade))
                conn.commit()
                st.success(f"Ingrediente '{nome}' cadastrado com sucesso!")
            except Error as e:
                st.error(f"Erro ao cadastrar ingrediente: {e}")
            finally:
                cursor.close()
                conn.close()

def cadastrar_produto():
    st.subheader("Cadastrar Produto")
    with st.form("form_produto", clear_on_submit=True):
        nome = st.text_input("Nome do produto")
        preco_venda = st.number_input("Preço de venda por unidade", step=0.01, value=None, placeholder="Ex: 5.00")
        quantidade = st.number_input("Quantidade por produção (ex: 10 fatias por bolo)", min_value=1, step=1)
        submit = st.form_submit_button("Cadastrar produto")

        if submit:
            if not nome or preco_venda is None or preco_venda <= 0 or quantidade <= 0:
                st.warning("Preencha todos os campos corretamente.")
                return

            conn = get_conn()
            if not conn:
                st.error("Erro ao conectar ao banco de dados.")
                return
            try:
                cursor = conn.cursor()
                sql = "INSERT INTO produtos (nome, preco_venda, quantidade_por_producao) VALUES (%s, %s, %s)"
                cursor.execute(sql, (nome, preco_venda, quantidade))
                conn.commit()
                st.success(f"Produto '{nome}' cadastrado com sucesso!")
            except Error as e:
                st.error(f"Erro ao cadastrar produto: {e}")
            finally:
                cursor.close()
                conn.close()

def montar_receita():
    st.subheader("Montar Receita do Produto")
    conn = get_conn()
    if not conn:
        st.error("Erro ao conectar ao banco")
        return
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome FROM produtos ORDER BY nome")
    produtos = cursor.fetchall()
    if not produtos:
        st.warning("Cadastre algum produto primeiro.")
        cursor.close()
        conn.close()
        return
    produto_dict = {nome: id for id, nome in produtos}
    produto_selecionado = st.selectbox("Produto", list(produto_dict.keys()))

    cursor.execute("SELECT id, nome, unidade_medida FROM ingredientes ORDER BY nome")
    ingredientes = cursor.fetchall()
    if not ingredientes:
        st.warning("Cadastre ingredientes primeiro.")
        cursor.close()
        conn.close()
        return
    ingrediente_dict = {nome: (id, unidade) for id, nome, unidade in ingredientes}
    ingrediente_selecionado = st.selectbox("Ingrediente", list(ingrediente_dict.keys()))

    quantidade = st.number_input("Quantidade usada", min_value=0.0, value=None, format="%.3f")

    if st.button("Adicionar ingrediente à receita"):
        if quantidade is None or quantidade <= 0:
            st.warning("Quantidade deve ser maior que zero.")
        else:
            produto_id = produto_dict[produto_selecionado]
            ingrediente_id = ingrediente_dict[ingrediente_selecionado][0]

            try:
                sql_check = "SELECT id FROM produtos_ingredientes WHERE produto_id = %s AND ingrediente_id = %s"
                cursor.execute(sql_check, (produto_id, ingrediente_id))
                existente = cursor.fetchone()

                if existente:
                    sql_update = "UPDATE produtos_ingredientes SET quantidade = quantidade + %s WHERE id = %s"
                    cursor.execute(sql_update, (quantidade, existente[0]))
                else:
                    sql_insert = "INSERT INTO produtos_ingredientes (produto_id, ingrediente_id, quantidade) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insert, (produto_id, ingrediente_id, quantidade))
                conn.commit()
                st.success(f"{ingrediente_selecionado} adicionado/atualizado na receita de {produto_selecionado}.")
            except Error as e:
                st.error(f"Erro ao atualizar receita: {e}")

    st.write(f"### Receita atual de {produto_selecionado}:")
    cursor.execute("""
        SELECT i.nome, r.quantidade, i.unidade_medida 
        FROM produtos_ingredientes r
        JOIN ingredientes i ON r.ingrediente_id = i.id
        WHERE r.produto_id = %s
    """, (produto_dict[produto_selecionado],))
    receita = cursor.fetchall()
    if receita:
        for nome_ing, qtd, unidade in receita:
            st.write(f"- {qtd} {unidade} de {nome_ing}")
    else:
        st.info("Nenhum ingrediente adicionado ainda.")

    cursor.close()
    conn.close()

def analisar_lucro():
    st.subheader("Análise de Lucro")
    conn = get_conn()
    if not conn:
        st.error("Erro ao conectar ao banco")
        return
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, preco_venda, quantidade_por_producao FROM produtos ORDER BY nome")
    produtos = cursor.fetchall()
    if not produtos:
        st.warning("Cadastre produtos primeiro.")
        cursor.close()
        conn.close()
        return

    produto_dict = {nome: (id, preco, qtd) for id, nome, preco, qtd in produtos}
    produto_nome = st.selectbox("Selecione o produto para análise", list(produto_dict.keys()))
    produto_id, preco_unitario, quantidade = produto_dict[produto_nome]

    cursor.execute("""
        SELECT r.quantidade, i.custo_unitario
        FROM produtos_ingredientes r
        JOIN ingredientes i ON r.ingrediente_id = i.id
        WHERE r.produto_id = %s
    """, (produto_id,))
    componentes = cursor.fetchall()

    custo_total = sum(qtd * custo for qtd, custo in componentes)
    receita_total = preco_unitario * quantidade
    lucro_total = receita_total - custo_total
    lucro_unitario = lucro_total / quantidade if quantidade > 0 else 0
    margem = (lucro_total / custo_total * 100) if custo_total > 0 else 0

    st.markdown(f"**Preço unitário de venda:** R$ {preco_unitario:.2f}")
    st.markdown(f"**Quantidade por produção:** {quantidade}")
    st.markdown(f"**Receita total:** R$ {receita_total:.2f}")
    st.markdown(f"**Custo total:** R$ {custo_total:.2f}")
    st.markdown(f"**Lucro total:** R$ {lucro_total:.2f}")
    st.markdown(f"**Lucro por unidade:** R$ {lucro_unitario:.2f}")
    st.markdown(f"**Margem de lucro:** {margem:.1f}%")

    cursor.close()
    conn.close()

def alterar_excluir():
    st.subheader("Alterar / Excluir")

    opcao = st.selectbox("Escolha o que deseja alterar ou excluir:", [
        "Ingrediente",
        "Produto",
        "Receita (Ingredientes do Produto)"
    ])

    conn = get_conn()
    if not conn:
        st.error("Erro ao conectar ao banco")
        return
    cursor = conn.cursor()

    if opcao == "Ingrediente":
        cursor.execute("SELECT id, nome, custo_unitario, unidade_medida FROM ingredientes ORDER BY nome")
        ingredientes = cursor.fetchall()
        if not ingredientes:
            st.info("Nenhum ingrediente cadastrado.")
            cursor.close()
            conn.close()
            return

        ingredientes_dict = {f"{nome} (R$ {float(custo_unitario):.2f} / {unidade})": (id, nome, float(custo_unitario), unidade) for id, nome, custo_unitario, unidade in ingredientes}
        selecionado = st.selectbox("Selecione o ingrediente", list(ingredientes_dict.keys()))
        id_sel, nome_sel, custo_sel, unidade_sel = ingredientes_dict[selecionado]

        acao = st.radio("Escolha a ação:", ["Alterar", "Excluir"])

        if acao == "Alterar":
            novo_nome = st.text_input("Nome", value=nome_sel)
            novo_custo = st.number_input("Custo unitário", step=0.01, value=float(custo_sel))
            nova_unidade = st.text_input("Unidade", value=unidade_sel)
            if st.button("Salvar alterações"):
                if not novo_nome or novo_custo <= 0 or not nova_unidade:
                    st.warning("Preencha todos os campos corretamente.")
                else:
                    try:
                        sql = "UPDATE ingredientes SET nome=%s, custo_unitario=%s, unidade_medida=%s WHERE id=%s"
                        cursor.execute(sql, (novo_nome, novo_custo, nova_unidade, id_sel))
                        conn.commit()
                        st.success("Ingrediente alterado com sucesso!")
                    except Error as e:
                        st.error(f"Erro ao alterar ingrediente: {e}")

        elif acao == "Excluir":
            if st.button("Excluir ingrediente"):
                try:
                    sql = "DELETE FROM ingredientes WHERE id=%s"
                    cursor.execute(sql, (id_sel,))
                    conn.commit()
                    st.success("Ingrediente excluído com sucesso!")
                except Error as e:
                    st.error(f"Erro ao excluir ingrediente: {e}")

    elif opcao == "Produto":
        cursor.execute("SELECT id, nome, preco_venda, quantidade_por_producao FROM produtos ORDER BY nome")
        produtos = cursor.fetchall()
        if not produtos:
            st.info("Nenhum produto cadastrado.")
            cursor.close()
            conn.close()
            return

        produtos_dict = {f"{nome} (R$ {float(preco_venda):.2f}, Qtd: {quantidade_por_producao})": (id, nome, float(preco_venda), quantidade_por_producao) for id, nome, preco_venda, quantidade_por_producao in produtos}
        selecionado = st.selectbox("Selecione o produto", list(produtos_dict.keys()))
        id_sel, nome_sel, preco_sel, qtd_sel = produtos_dict[selecionado]

        acao = st.radio("Escolha a ação:", ["Alterar", "Excluir"])

        if acao == "Alterar":
            novo_nome = st.text_input("Nome", value=nome_sel)
            novo_preco = st.number_input("Preço de venda", step=0.01, value=float(preco_sel))
            nova_qtd = st.number_input("Quantidade por produção", min_value=1, step=1, value=int(qtd_sel))
            if st.button("Salvar alterações"):
                if not novo_nome or novo_preco <= 0 or nova_qtd <= 0:
                    st.warning("Preencha todos os campos corretamente.")
                else:
                    try:
                        sql = "UPDATE produtos SET nome=%s, preco_venda=%s, quantidade_por_producao=%s WHERE id=%s"
                        cursor.execute(sql, (novo_nome, novo_preco, nova_qtd, id_sel))
                        conn.commit()
                        st.success("Produto alterado com sucesso!")
                    except Error as e:
                        st.error(f"Erro ao alterar produto: {e}")

        elif acao == "Excluir":
            if st.button("Excluir produto"):
                try:
                    sql = "DELETE FROM produtos WHERE id=%s"
                    cursor.execute(sql, (id_sel,))
                    conn.commit()
                    st.success("Produto excluído com sucesso!")
                except Error as e:
                    st.error(f"Erro ao excluir produto: {e}")

    elif opcao == "Receita (Ingredientes do Produto)":
        cursor.execute("SELECT id, nome FROM produtos ORDER BY nome")
        produtos = cursor.fetchall()
        if not produtos:
            st.info("Nenhum produto cadastrado.")
            cursor.close()
            conn.close()
            return

        produto_dict = {nome: id for id, nome in produtos}
        produto_selecionado = st.selectbox("Selecione o produto", list(produto_dict.keys()))
        produto_id = produto_dict[produto_selecionado]

        cursor.execute("""
            SELECT r.id, i.nome, r.quantidade, i.unidade_medida
            FROM produtos_ingredientes r
            JOIN ingredientes i ON r.ingrediente_id = i.id
            WHERE r.produto_id = %s
            ORDER BY i.nome
        """, (produto_id,))
        ingredientes_receita = cursor.fetchall()

        if not ingredientes_receita:
            st.info("Nenhum ingrediente cadastrado para esse produto.")
            cursor.close()
            conn.close()
            return

        ingredientes_dict = {f"{nome} - {float(quantidade):.3f} {unidade}": (id_receita, float(quantidade)) for id_receita, nome, quantidade, unidade in ingredientes_receita}
        selecionado = st.selectbox("Selecione o ingrediente da receita", list(ingredientes_dict.keys()))
        id_receita_sel, qtd_sel = ingredientes_dict[selecionado]

        acao = st.radio("Escolha a ação:", ["Alterar quantidade", "Excluir ingrediente"])

        if acao == "Alterar quantidade":
            nova_qtd = st.number_input("Nova quantidade usada", min_value=0.001, format="%.3f", value=float(qtd_sel))
            if st.button("Salvar alteração"):
                try:
                    sql = "UPDATE produtos_ingredientes SET quantidade=%s WHERE id=%s"
                    cursor.execute(sql, (nova_qtd, id_receita_sel))
                    conn.commit()
                    st.success("Quantidade alterada com sucesso!")
                except Error as e:
                    st.error(f"Erro ao alterar quantidade: {e}")

        elif acao == "Excluir ingrediente":
            if st.button("Excluir ingrediente da receita"):
                try:
                    sql = "DELETE FROM produtos_ingredientes WHERE id=%s"
                    cursor.execute(sql, (id_receita_sel,))
                    conn.commit()
                    st.success("Ingrediente excluído da receita com sucesso!")
                except Error as e:
                    st.error(f"Erro ao excluir ingrediente: {e}")

    cursor.close()
    conn.close()

def main():
    st.title("📦 Produção e Lucro")
    aba = st.radio("Escolha uma funcionalidade:", [
        "Cadastrar Ingrediente",
        "Cadastrar Produto",
        "Montar Receita",
        "Alterar / Excluir",
        "Análise de Lucro"
    ])

    if aba == "Cadastrar Ingrediente":
        cadastrar_ingrediente()
    elif aba == "Cadastrar Produto":
        cadastrar_produto()
    elif aba == "Montar Receita":
        montar_receita()
    elif aba == "Alterar / Excluir":
        alterar_excluir()
    elif aba == "Análise de Lucro":
        analisar_lucro()

if __name__ == "__main__":
    main()