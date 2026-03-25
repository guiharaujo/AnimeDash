import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render() -> None:
    st.title("Graficos e Analises")

    df = st.session_state.animes_df

    tab1, tab2, tab3 = st.tabs(["Generos", "Estudios", "Ano / Temporada"])

    # -----------------------------------------------------------------------
    # TAB 1: Generos
    # -----------------------------------------------------------------------
    with tab1:
        genre_series = (
            df["generos"].dropna()
            .str.split(", ")
            .explode()
            .str.strip()
        )
        genre_counts = genre_series.value_counts().reset_index()
        genre_counts.columns = ["Genero", "Quantidade"]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top 20 Generos por Quantidade")
            top20 = genre_counts.head(20)
            fig = px.bar(
                top20, x="Quantidade", y="Genero", orientation="h",
                color="Quantidade", color_continuous_scale="Blues",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Distribuicao (Top 10 + Outros)")
            top10 = genre_counts.head(10).copy()
            outros = pd.DataFrame([{"Genero": "Outros", "Quantidade": genre_counts.iloc[10:]["Quantidade"].sum()}])
            pie_df = pd.concat([top10, outros], ignore_index=True)
            fig2 = px.pie(pie_df, values="Quantidade", names="Genero", hole=0.35)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Nota Media por Genero (Top 15)")
        genre_note_rows = []
        for _, row in df.iterrows():
            if not row["generos"] or pd.isna(row["nota"]):
                continue
            for g in str(row["generos"]).split(", "):
                g = g.strip()
                if g:
                    genre_note_rows.append({"Genero": g, "nota": row["nota"]})

        if genre_note_rows:
            gndf = pd.DataFrame(genre_note_rows)
            genre_avg = gndf.groupby("Genero")["nota"].agg(["mean", "count"]).reset_index()
            genre_avg.columns = ["Genero", "Nota Media", "Quantidade"]
            genre_avg = genre_avg[genre_avg["Quantidade"] >= 5].sort_values("Nota Media", ascending=False).head(15)
            fig3 = px.bar(
                genre_avg, x="Genero", y="Nota Media",
                color="Nota Media", color_continuous_scale="RdYlGn", text="Nota Media",
            )
            fig3.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig3.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------------------------------------------------
    # TAB 2: Estudios
    # -----------------------------------------------------------------------
    with tab2:
        studio_df = df[df["estudio"].notna() & (df["estudio"] != "")]

        studio_counts = studio_df.groupby("estudio").agg(
            Quantidade=("id", "count"),
            Nota_Media=("nota", "mean"),
            Popularidade_Total=("popularidade", "sum"),
        ).reset_index().sort_values("Quantidade", ascending=False).head(20)
        studio_counts["Nota_Media"] = studio_counts["Nota_Media"].round(1)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 20 Estudios por Animes")
            fig4 = px.bar(
                studio_counts, x="Quantidade", y="estudio", orientation="h",
                color="Nota_Media", color_continuous_scale="RdYlGn",
                hover_data=["Nota_Media"],
                labels={"estudio": "Estudio", "Nota_Media": "Nota Media"},
            )
            fig4.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            st.subheader("Quantidade x Nota Media")
            fig5 = px.scatter(
                studio_counts, x="Quantidade", y="Nota_Media",
                size="Popularidade_Total", hover_name="estudio",
                color="Nota_Media", color_continuous_scale="RdYlGn",
                labels={"Quantidade": "Nr de Animes", "Nota_Media": "Nota Media"},
            )
            st.plotly_chart(fig5, use_container_width=True)

    # -----------------------------------------------------------------------
    # TAB 3: Ano / Temporada
    # -----------------------------------------------------------------------
    with tab3:
        year_df = df[df["ano"].notna() & (df["ano"] >= 1990)].copy()
        year_df["ano"] = year_df["ano"].astype(int)

        st.subheader("Animes por Ano")
        year_counts = year_df.groupby("ano").size().reset_index(name="Quantidade")
        fig6 = px.line(year_counts, x="ano", y="Quantidade", markers=True,
                       labels={"ano": "Ano", "Quantidade": "Nr de Animes"})
        st.plotly_chart(fig6, use_container_width=True)

        st.subheader("Animes por Ano e Temporada")
        season_year_df = year_df[year_df["temporada"].notna()].copy()
        season_counts = season_year_df.groupby(["ano", "temporada"]).size().reset_index(name="Quantidade")
        season_order = ["WINTER", "SPRING", "SUMMER", "FALL"]
        season_colors = {"WINTER": "#74b9ff", "SPRING": "#55efc4", "SUMMER": "#fdcb6e", "FALL": "#e17055"}
        fig7 = px.bar(
            season_counts, x="ano", y="Quantidade", color="temporada",
            barmode="stack", category_orders={"temporada": season_order},
            color_discrete_map=season_colors, labels={"ano": "Ano", "temporada": "Temporada"},
        )
        st.plotly_chart(fig7, use_container_width=True)

        st.subheader("Nota Media por Ano e Temporada")
        if not season_year_df.empty:
            heat_df = season_year_df[season_year_df["nota"].notna()].groupby(
                ["ano", "temporada"])["nota"].mean().reset_index()
            heat_pivot = heat_df.pivot(index="temporada", columns="ano", values="nota")
            heat_pivot = heat_pivot.reindex(season_order)
            fig8 = go.Figure(data=go.Heatmap(
                z=heat_pivot.values,
                x=[str(c) for c in heat_pivot.columns],
                y=heat_pivot.index.tolist(),
                colorscale="RdYlGn", zmin=50, zmax=90,
                text=[[f"{v:.0f}" if v == v else "" for v in row] for row in heat_pivot.values],
                texttemplate="%{text}",
            ))
            fig8.update_layout(xaxis_title="Ano", yaxis_title="Temporada")
            st.plotly_chart(fig8, use_container_width=True)
