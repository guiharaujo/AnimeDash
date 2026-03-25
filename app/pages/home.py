import streamlit as st
import plotly.express as px


def render() -> None:
    st.title("AnimeDash - Estatisticas Gerais")

    stats = st.session_state.stats
    df = st.session_state.animes_df

    # --- Métricas ---
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de Animes", stats["total_animes"])
    c2.metric("Nota Media", f"{stats['avg_score']:.1f}")
    c3.metric("Genero Top", stats["top_genre"])
    c4.metric("Estudio Top", stats["top_studio"])
    c5.metric("Em Exibicao", stats["animes_releasing"])

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Generos")
        genre_series = (
            df["generos"].dropna()
            .str.split(", ")
            .explode()
            .str.strip()
        )
        genre_counts = genre_series.value_counts().head(10).reset_index()
        genre_counts.columns = ["Genero", "Quantidade"]
        fig = px.bar(
            genre_counts,
            x="Quantidade",
            y="Genero",
            orientation="h",
            color="Quantidade",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Nota x Popularidade")
        scatter_df = df[df["nota"].notna()].copy()
        fig2 = px.scatter(
            scatter_df,
            x="popularidade",
            y="nota",
            hover_name="titulo",
            hover_data={"generos": True, "estudio": True},
            color="nota",
            color_continuous_scale="RdYlGn",
            labels={"popularidade": "Popularidade", "nota": "Nota (0-100)"},
        )
        fig2.update_traces(marker={"size": 5, "opacity": 0.7})
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Distribuicao por Status")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Quantidade"]
    fig3 = px.pie(status_counts, values="Quantidade", names="Status", hole=0.4)
    st.plotly_chart(fig3, use_container_width=True)
