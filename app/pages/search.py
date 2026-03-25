import streamlit as st
import pyodbc

from database.repository import get_anime_by_name


def render(conn: pyodbc.Connection) -> None:
    st.title("Busca de Animes")

    query = st.text_input("Digite o nome do anime", placeholder="Ex: Naruto, Attack on Titan")

    if not query or len(query) < 2:
        st.info("Digite pelo menos 2 caracteres para buscar.")
        return

    results = get_anime_by_name(conn, query)

    if results.empty:
        st.warning(f"Nenhum resultado encontrado para '{query}'.")
        return

    st.success(f"{len(results)} resultado(s) encontrado(s) para '{query}'")

    for _, row in results.iterrows():
        title = row["titulo"] or "Sem titulo"
        original = f" ({row['titulo_original']})" if row["titulo_original"] else ""

        with st.expander(f"{title}{original}"):
            col1, col2 = st.columns([1, 3])

            with col1:
                if row["capa_url"]:
                    st.image(row["capa_url"], width=150)

            with col2:
                nota = f"{row['nota']:.0f}/100" if row["nota"] else "N/A"
                pop = f"{int(row['popularidade']):,}" if row["popularidade"] else "N/A"
                eps = str(int(row["episodios"])) if row["episodios"] else "N/A"

                ca, cb, cc = st.columns(3)
                ca.metric("Nota", nota)
                cb.metric("Popularidade", pop)
                cc.metric("Episodios", eps)

                st.write(f"**Generos:** {row['generos'] or 'N/A'}")
                st.write(f"**Estudio:** {row['estudio'] or 'N/A'}")
                st.write(f"**Status:** {row['status'] or 'N/A'}")

                temporada = row["temporada"] or ""
                ano = str(int(row["ano"])) if row["ano"] else ""
                periodo = f"{temporada} {ano}".strip() or "N/A"
                st.write(f"**Temporada:** {periodo}")

                if row["descricao"]:
                    desc = str(row["descricao"])
                    if len(desc) > 500:
                        desc = desc[:500] + "..."
                    st.write(f"**Descricao:** {desc}")
