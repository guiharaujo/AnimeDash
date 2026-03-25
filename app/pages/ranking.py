import streamlit as st


def render() -> None:
    st.title("Ranking de Animes")

    df = st.session_state.animes_df

    sort_by = st.radio("Ordenar por", ["Popularidade", "Nota"], horizontal=True)

    if sort_by == "Nota":
        sorted_df = df[df["nota"].notna()].sort_values("nota", ascending=False).reset_index(drop=True)
    else:
        sorted_df = df[df["popularidade"].notna()].sort_values("popularidade", ascending=False).reset_index(drop=True)

    page_size = 50
    total_pages = max(1, (len(sorted_df) + page_size - 1) // page_size)
    page = st.selectbox("Pagina", list(range(1, total_pages + 1)), index=0)

    start = (page - 1) * page_size
    end = start + page_size
    page_df = sorted_df.iloc[start:end].copy()
    page_df.insert(0, "Posicao", range(start + 1, start + len(page_df) + 1))

    st.dataframe(
        page_df[["Posicao", "capa_url", "titulo", "titulo_original", "nota",
                 "popularidade", "generos", "estudio", "episodios", "status", "ano"]],
        column_config={
            "capa_url":        st.column_config.ImageColumn("Capa", width="small"),
            "titulo":          st.column_config.TextColumn("Titulo"),
            "titulo_original": st.column_config.TextColumn("Titulo Original"),
            "nota":            st.column_config.ProgressColumn("Nota", min_value=0, max_value=100, format="%d"),
            "popularidade":    st.column_config.NumberColumn("Popularidade", format="%d"),
            "episodios":       st.column_config.NumberColumn("Eps."),
            "generos":         st.column_config.TextColumn("Generos"),
            "estudio":         st.column_config.TextColumn("Estudio"),
            "status":          st.column_config.TextColumn("Status"),
            "ano":             st.column_config.NumberColumn("Ano"),
        },
        hide_index=True,
        use_container_width=True,
        height=600,
    )
