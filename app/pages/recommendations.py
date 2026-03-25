import streamlit as st
import pyodbc

from recommendation.engine import get_recommendations


def render(conn: pyodbc.Connection) -> None:
    st.title("Sistema de Recomendacao")
    st.write("Digite o nome de um anime e receba 10 sugestoes baseadas em generos e tags similares.")

    query = st.text_input("Nome do anime", placeholder="Ex: Naruto, Death Note, Fullmetal Alchemist")

    if st.button("Recomendar", type="primary") and query:
        with st.spinner("Calculando recomendacoes..."):
            found_title, recs_df = get_recommendations(query, conn, top_n=10)

        if found_title is None:
            st.error(f"Anime '{query}' nao encontrado no banco de dados.")
            return

        if recs_df is None or recs_df.empty:
            st.warning(f"Nao foi possivel calcular recomendacoes para '{found_title}'.")
            return

        st.success(f"Recomendacoes baseadas em: {found_title}")
        st.divider()

        for i, (_, row) in enumerate(recs_df.iterrows(), start=1):
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                if row["capa_url"]:
                    st.image(row["capa_url"], width=100)

            with col2:
                titulo = row["titulo"] or "Sem titulo"
                original = f" ({row['titulo_original']})" if row["titulo_original"] else ""
                st.markdown(f"**{i}. {titulo}**{original}")
                st.write(f"Generos: {row['generos'] or 'N/A'}")
                nota = f"{row['nota']:.0f}/100" if row["nota"] else "N/A"
                st.write(f"Estudio: {row['estudio'] or 'N/A'} | Nota: {nota}")

            with col3:
                st.metric("Similaridade", row["similaridade_pct"])

            st.divider()
