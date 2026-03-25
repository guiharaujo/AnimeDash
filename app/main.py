import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pyodbc

from database.connection import get_connection

st.set_page_config(
    page_title="AnimeDash",
    page_icon="AnimeDash",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helpers de banco (sem pd.read_sql para evitar warnings do pandas 2.x)
# ---------------------------------------------------------------------------

def _query_df(conn, sql, params=None):
    cursor = conn.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return pd.DataFrame.from_records(rows, columns=cols)


def _load_all_animes(conn):
    return _query_df(conn, "SELECT * FROM Animes ORDER BY popularidade DESC")


def _load_anime_tags(conn):
    return _query_df(conn, """
        SELECT at.id_anime, at.id_tag, at.rank, t.nome
        FROM Anime_Tags at JOIN Tags t ON at.id_tag = t.id
    """)


def _load_stats(conn):
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Animes")
    total = cur.fetchone()[0]

    cur.execute("SELECT AVG(CAST(nota AS FLOAT)) FROM Animes WHERE nota IS NOT NULL")
    avg = cur.fetchone()[0] or 0.0

    cur.execute("""
        SELECT TOP 1 value, COUNT(*) cnt FROM Animes
        CROSS APPLY STRING_SPLIT(generos, ',')
        WHERE generos IS NOT NULL AND generos != ''
        GROUP BY value ORDER BY cnt DESC
    """)
    row = cur.fetchone()
    top_genre = row[0].strip() if row else "N/A"

    cur.execute("""
        SELECT TOP 1 estudio, COUNT(*) cnt FROM Animes
        WHERE estudio IS NOT NULL AND estudio != ''
        GROUP BY estudio ORDER BY cnt DESC
    """)
    row = cur.fetchone()
    top_studio = row[0] if row else "N/A"

    cur.execute("SELECT COUNT(*) FROM Tags")
    total_tags = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Animes WHERE status = 'RELEASING'")
    releasing = cur.fetchone()[0]

    return {
        "total_animes": int(total),
        "avg_score": round(float(avg), 1),
        "top_genre": top_genre,
        "top_studio": top_studio,
        "total_tags": int(total_tags),
        "animes_releasing": int(releasing),
    }


def _render_anime_popup(row, df):
    """Conteudo do popover ao clicar em um anime."""
    c_img, c_info = st.columns([1, 2])
    with c_img:
        if row["capa_url"]:
            st.image(row["capa_url"], width=120)
    with c_info:
        st.markdown(f"**{row['titulo']}**")
        if row["titulo_original"]:
            st.caption(row["titulo_original"])
        eps  = f"{int(row['episodios'])} eps" if row["episodios"] else "Em andamento"
        nota = f"{row['nota']:.0f}/100"       if row["nota"]      else "N/A"
        st.write(f"Episodios: **{eps}**")
        st.write(f"Nota: **{nota}**")
        st.write(f"Generos: {row['generos'] or 'N/A'}")
        st.write(f"Estudio: {row['estudio'] or 'N/A'}")

    if row["descricao"]:
        st.caption(str(row["descricao"])[:300] + "...")

    # 1 anime recomendado por genero
    generos_anime = set(str(row["generos"] or "").split(", "))
    candidatos = df[df["id"] != row["id"]].copy()
    candidatos["match"] = candidatos["generos"].apply(
        lambda g: len(generos_anime & set(str(g or "").split(", ")))
    )
    rec = candidatos[candidatos["match"] > 0].sort_values(
        ["match", "nota"], ascending=False
    ).iloc[0] if not candidatos[candidatos["match"] > 0].empty else None

    if rec is not None:
        st.divider()
        st.write("**Recomendado:**")
        r1, r2 = st.columns([1, 3])
        with r1:
            if rec["capa_url"]:
                st.image(rec["capa_url"], width=60)
        with r2:
            st.write(f"**{rec['titulo']}**")
            st.caption(f"{rec['generos'] or ''} | Nota: {rec['nota']:.0f}" if rec["nota"] else rec["generos"] or "")


def _search_animes(conn, name):
    pattern = f"%{name}%"
    return _query_df(conn,
        "SELECT * FROM Animes WHERE titulo LIKE ? OR titulo_original LIKE ? ORDER BY popularidade DESC",
        (pattern, pattern))


# ---------------------------------------------------------------------------
# Carregar dados uma vez no session_state
# ---------------------------------------------------------------------------

DATA_VERSION = "v3"

# Força recarga se session_state estiver com chaves de versão antiga
if st.session_state.get("_data_version") != DATA_VERSION:
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.session_state["_data_version"] = DATA_VERSION

if "conn" not in st.session_state:
    try:
        st.session_state.conn = get_connection()
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        st.stop()

if "df" not in st.session_state:
    try:
        c = st.session_state.conn
        st.session_state.df = _load_all_animes(c)
        st.session_state.tags_df = _load_anime_tags(c)
        st.session_state.stats = _load_stats(c)
    except Exception as e:
        import traceback
        st.error(f"Erro ao carregar dados: {e}")
        st.code(traceback.format_exc())
        st.stop()

# Garante que as chaves existem antes de usar
if "df" not in st.session_state or "tags_df" not in st.session_state or "stats" not in st.session_state:
    st.error("Dados nao carregados. Recarregue a pagina.")
    st.stop()

conn = st.session_state.conn
df = st.session_state.df
tags_df = st.session_state.tags_df
stats = st.session_state.stats

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("AnimeDash")
    st.caption("Top 500 Animes - AniList")
    st.divider()
    page = st.radio(
        "nav",
        ["Inicio", "Ranking", "Graficos", "Busca", "Recomendacoes"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Fonte: AniList GraphQL API")

# ---------------------------------------------------------------------------
# PAGINA: Inicio
# ---------------------------------------------------------------------------

if page == "Inicio":
    st.header("Estatisticas Gerais")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de Animes", stats["total_animes"])
    c2.metric("Nota Media", f"{stats['avg_score']:.1f}")
    c3.metric("Genero Top", stats["top_genre"])
    c4.metric("Estudio Top", stats["top_studio"])
    c5.metric("Em Exibicao", stats["animes_releasing"])

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Animes Mais Assistidos")
        top10 = df.nlargest(10, "popularidade").reset_index(drop=True)
        for i in range(0, 10, 2):
            c_a, c_b = st.columns(2)
            for col_card, idx in zip([c_a, c_b], [i, i + 1]):
                if idx < len(top10):
                    row = top10.iloc[idx]
                    with col_card:
                        if row["capa_url"]:
                            st.image(row["capa_url"], width=80)
                        with st.popover(f"#{idx+1} {row['titulo'][:22]}"):
                            _render_anime_popup(row, df)

    with col2:
        st.subheader("Nota x Popularidade")
        sdf = df[df["nota"].notna()].copy()
        fig2 = px.scatter(sdf, x="popularidade", y="nota", hover_name="titulo",
                          color="nota", color_continuous_scale="RdYlGn",
                          labels={"popularidade": "Popularidade", "nota": "Nota"})
        fig2.update_traces(marker={"size": 5, "opacity": 0.7})
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Top 5 Animes com Mais Episodios")
    top5_eps = df[df["episodios"].notna()].nlargest(5, "episodios").reset_index(drop=True)
    cols_eps = st.columns(5)
    for i, col_card in enumerate(cols_eps):
        if i < len(top5_eps):
            row = top5_eps.iloc[i]
            with col_card:
                if row["capa_url"]:
                    st.image(row["capa_url"], use_container_width=True)
                with st.popover(f"#{i+1} {row['titulo'][:18]}"):
                    _render_anime_popup(row, df)

# ---------------------------------------------------------------------------
# PAGINA: Ranking
# ---------------------------------------------------------------------------

elif page == "Ranking":
    st.header("Ranking de Animes")

    sort_by = st.radio("Ordenar por", ["Popularidade", "Nota"], horizontal=True)
    if sort_by == "Nota":
        sdf = df[df["nota"].notna()].sort_values("nota", ascending=False).reset_index(drop=True)
    else:
        sdf = df.sort_values("popularidade", ascending=False).reset_index(drop=True)

    page_size = 50
    total_pages = max(1, (len(sdf) + page_size - 1) // page_size)
    pnum = st.selectbox("Pagina", list(range(1, total_pages + 1)))
    start = (pnum - 1) * page_size
    pdf = sdf.iloc[start:start + page_size].copy()
    pdf.insert(0, "Pos", range(start + 1, start + len(pdf) + 1))

    st.dataframe(
        pdf[["Pos", "capa_url", "titulo", "titulo_original", "nota",
             "popularidade", "generos", "estudio", "episodios", "status", "ano"]],
        column_config={
            "capa_url":        st.column_config.ImageColumn("Capa", width="small"),
            "titulo":          "Titulo",
            "titulo_original": "Titulo Original",
            "nota":            st.column_config.ProgressColumn("Nota", min_value=0, max_value=100, format="%d"),
            "popularidade":    st.column_config.NumberColumn("Popularidade", format="%d"),
            "episodios":       "Eps",
            "generos":         "Generos",
            "estudio":         "Estudio",
            "status":          "Status",
            "ano":             "Ano",
        },
        hide_index=True,
        use_container_width=True,
        height=600,
    )

# ---------------------------------------------------------------------------
# PAGINA: Graficos
# ---------------------------------------------------------------------------

elif page == "Graficos":
    st.header("Graficos e Analises")

    tab1, tab2, tab3 = st.tabs(["Generos", "Estudios", "Ano / Temporada"])

    with tab1:
        gs = df["generos"].dropna().str.split(", ").explode().str.strip()
        gc = gs.value_counts().reset_index()
        gc.columns = ["Genero", "Qtd"]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 20 Generos")
            fig = px.bar(gc.head(20), x="Qtd", y="Genero", orientation="h",
                         color="Qtd", color_continuous_scale="Blues")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Distribuicao Top 10 + Outros")
            top10 = gc.head(10).copy()
            outros = pd.DataFrame([{"Genero": "Outros", "Qtd": gc.iloc[10:]["Qtd"].sum()}])
            pie_df = pd.concat([top10, outros], ignore_index=True)
            fig2 = px.pie(pie_df, values="Qtd", names="Genero", hole=0.35)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Nota Media por Genero (Top 15)")
        rows_gn = []
        for _, row in df.iterrows():
            if not row["generos"] or pd.isna(row["nota"]):
                continue
            for g in str(row["generos"]).split(", "):
                g = g.strip()
                if g:
                    rows_gn.append({"Genero": g, "nota": row["nota"]})
        if rows_gn:
            gndf = pd.DataFrame(rows_gn)
            gav = gndf.groupby("Genero")["nota"].agg(["mean", "count"]).reset_index()
            gav.columns = ["Genero", "Nota_Media", "Qtd"]
            gav = gav[gav["Qtd"] >= 5].sort_values("Nota_Media", ascending=False).head(15)
            fig3 = px.bar(gav, x="Genero", y="Nota_Media", color="Nota_Media",
                          color_continuous_scale="RdYlGn", text="Nota_Media")
            fig3.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig3.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        sdf2 = df[df["estudio"].notna() & (df["estudio"] != "")]
        sc2 = sdf2.groupby("estudio").agg(
            Qtd=("id", "count"),
            Nota_Media=("nota", "mean"),
            Pop_Total=("popularidade", "sum"),
        ).reset_index().sort_values("Qtd", ascending=False).head(20)
        sc2["Nota_Media"] = sc2["Nota_Media"].round(1)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 20 Estudios")
            fig4 = px.bar(sc2, x="Qtd", y="estudio", orientation="h",
                          color="Nota_Media", color_continuous_scale="RdYlGn",
                          labels={"estudio": "Estudio", "Nota_Media": "Nota Media"})
            fig4.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            st.subheader("Quantidade x Nota Media (Bubble)")
            fig5 = px.scatter(sc2, x="Qtd", y="Nota_Media", size="Pop_Total",
                              hover_name="estudio", color="Nota_Media",
                              color_continuous_scale="RdYlGn")
            st.plotly_chart(fig5, use_container_width=True)

    with tab3:
        ydf = df[df["ano"].notna() & (df["ano"] >= 1990)].copy()
        ydf["ano"] = ydf["ano"].astype(int)

        st.subheader("Animes por Ano")
        yc = ydf.groupby("ano").size().reset_index(name="Qtd")
        fig6 = px.line(yc, x="ano", y="Qtd", markers=True)
        st.plotly_chart(fig6, use_container_width=True)

        st.subheader("Animes por Ano e Temporada")
        sydf = ydf[ydf["temporada"].notna()].copy()
        ssc = sydf.groupby(["ano", "temporada"]).size().reset_index(name="Qtd")
        fig7 = px.bar(ssc, x="ano", y="Qtd", color="temporada", barmode="stack",
                      color_discrete_map={"WINTER": "#74b9ff", "SPRING": "#55efc4",
                                          "SUMMER": "#fdcb6e", "FALL": "#e17055"})
        st.plotly_chart(fig7, use_container_width=True)

        st.subheader("Nota Media por Ano e Temporada (Heatmap)")
        if not sydf.empty:
            hdf = sydf[sydf["nota"].notna()].groupby(["ano", "temporada"])["nota"].mean().reset_index()
            hp = hdf.pivot(index="temporada", columns="ano", values="nota")
            hp = hp.reindex(["WINTER", "SPRING", "SUMMER", "FALL"])
            fig8 = go.Figure(data=go.Heatmap(
                z=hp.values, x=[str(c) for c in hp.columns], y=hp.index.tolist(),
                colorscale="RdYlGn", zmin=50, zmax=90,
                text=[[f"{v:.0f}" if v == v else "" for v in row] for row in hp.values],
                texttemplate="%{text}",
            ))
            st.plotly_chart(fig8, use_container_width=True)

# ---------------------------------------------------------------------------
# PAGINA: Busca
# ---------------------------------------------------------------------------

elif page == "Busca":
    st.header("Busca de Animes")

    query = st.text_input("Nome do anime", placeholder="Ex: Naruto, Attack on Titan")

    if query and len(query) >= 2:
        results = _search_animes(conn, query)
        if results.empty:
            st.warning(f"Nenhum resultado para '{query}'.")
        else:
            st.success(f"{len(results)} resultado(s) para '{query}'")
            for _, row in results.iterrows():
                title = row["titulo"] or "Sem titulo"
                orig = f" ({row['titulo_original']})" if row["titulo_original"] else ""
                with st.expander(f"{title}{orig}"):
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        if row["capa_url"]:
                            st.image(row["capa_url"], width=150)
                    with c2:
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
                        if row["descricao"]:
                            desc = str(row["descricao"])[:500]
                            st.write(f"**Descricao:** {desc}...")
    else:
        st.info("Digite pelo menos 2 caracteres para buscar.")

# ---------------------------------------------------------------------------
# PAGINA: Recomendacoes
# ---------------------------------------------------------------------------

elif page == "Recomendacoes":
    st.header("Sistema de Recomendacao")
    st.write("Digite um anime e receba 10 sugestoes baseadas em generos e tags similares.")

    import numpy as np

    query = st.text_input("Nome do anime", placeholder="Ex: Naruto, Death Note")

    if st.button("Recomendar", type="primary") and query:
        matches = _search_animes(conn, query)
        if matches.empty:
            st.error(f"Anime '{query}' nao encontrado.")
        else:
            found = matches.sort_values("popularidade", ascending=False).iloc[0]
            found_id = int(found["id"])
            found_title = found["titulo"]

            with st.spinner("Calculando recomendacoes..."):
                # Construir matriz de features
                genre_rows = []
                for _, row in df.iterrows():
                    for g in str(row["generos"] or "").split(", "):
                        g = g.strip()
                        if g:
                            genre_rows.append({"id": row["id"], "feat": f"g__{g}", "w": 1.0})

                tag_rows = []
                for _, row in tags_df.iterrows():
                    rank = row["rank"] if row["rank"] is not None else 0
                    tag_rows.append({"id": row["id_anime"], "feat": f"t__{row['nome']}", "w": rank / 100.0})

                all_rows = pd.DataFrame(genre_rows + tag_rows)
                if all_rows.empty:
                    st.warning("Dados insuficientes para recomendacao.")
                else:
                    matrix = all_rows.pivot_table(index="id", columns="feat", values="w",
                                                   aggfunc="max", fill_value=0)

                    if found_id not in matrix.index:
                        st.warning("Anime sem features suficientes para recomendacao.")
                    else:
                        q_vec = matrix.loc[found_id].values.astype(float)
                        all_vecs = matrix.values.astype(float)
                        ids = matrix.index.tolist()

                        q_norm = np.linalg.norm(q_vec)
                        if q_norm == 0:
                            st.warning("Sem features para calcular similaridade.")
                        else:
                            norms = np.linalg.norm(all_vecs, axis=1)
                            norms[norms == 0] = 1e-10
                            sims = all_vecs.dot(q_vec) / (norms * q_norm)
                            pairs = [(ids[i], float(sims[i])) for i in range(len(ids)) if ids[i] != found_id]
                            pairs.sort(key=lambda x: x[1], reverse=True)
                            top10 = pairs[:10]

                            rec_ids = [p[0] for p in top10]
                            score_map = {p[0]: p[1] for p in top10}
                            recs = df[df["id"].isin(rec_ids)].copy()
                            recs["sim"] = recs["id"].map(score_map)
                            recs = recs.sort_values("sim", ascending=False)

                            st.success(f"Recomendacoes baseadas em: **{found_title}**")
                            st.divider()

                            for i, (_, row) in enumerate(recs.iterrows(), 1):
                                c1, c2, c3 = st.columns([1, 4, 1])
                                with c1:
                                    if row["capa_url"]:
                                        st.image(row["capa_url"], width=100)
                                with c2:
                                    st.markdown(f"**{i}. {row['titulo']}**")
                                    st.write(f"Generos: {row['generos'] or 'N/A'}")
                                    nota = f"{row['nota']:.0f}/100" if row["nota"] else "N/A"
                                    st.write(f"Estudio: {row['estudio'] or 'N/A'} | Nota: {nota}")
                                with c3:
                                    st.metric("Similaridade", f"{row['sim']*100:.1f}%")
                                st.divider()
