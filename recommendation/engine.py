import numpy as np
import pandas as pd
import pyodbc

from database.repository import get_all_animes, get_anime_by_name, get_all_anime_tags_bulk


def build_feature_matrix(animes_df: pd.DataFrame, anime_tags_df: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói uma matriz de features onde:
    - Linhas = id dos animes
    - Colunas = gêneros (peso 1.0) + tags (peso rank/100)
    """
    # --- Gêneros (features binárias) ---
    genre_rows = []
    for _, row in animes_df.iterrows():
        genres = str(row["generos"] or "").split(", ")
        for g in genres:
            g = g.strip()
            if g:
                genre_rows.append({"id": row["id"], "feature": f"g__{g}", "weight": 1.0})

    genre_df = pd.DataFrame(genre_rows) if genre_rows else pd.DataFrame(columns=["id", "feature", "weight"])

    # --- Tags (features ponderadas) ---
    tag_rows = []
    for _, row in anime_tags_df.iterrows():
        rank = row["rank"] if row["rank"] is not None else 0
        tag_rows.append({
            "id":      row["id_anime"],
            "feature": f"t__{row['nome']}",
            "weight":  round(rank / 100.0, 4),
        })

    tag_df = pd.DataFrame(tag_rows) if tag_rows else pd.DataFrame(columns=["id", "feature", "weight"])

    # --- Combinar e fazer pivot ---
    combined = pd.concat([genre_df, tag_df], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(index=animes_df["id"])

    matrix = combined.pivot_table(index="id", columns="feature", values="weight", aggfunc="max", fill_value=0)
    return matrix


def compute_similarity(feature_matrix: pd.DataFrame, query_anime_id: int, top_n: int = 10) -> list[tuple]:
    """
    Calcula cosine similarity entre o anime query e todos os outros.
    Retorna lista de (anime_id, score) ordenada decrescente.
    """
    if query_anime_id not in feature_matrix.index:
        return []

    query_vec = feature_matrix.loc[query_anime_id].values.astype(float)
    all_vecs = feature_matrix.values.astype(float)
    ids = feature_matrix.index.tolist()

    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return []

    all_norms = np.linalg.norm(all_vecs, axis=1)
    all_norms[all_norms == 0] = 1e-10  # evitar divisão por zero

    dot_products = all_vecs.dot(query_vec)
    similarities = dot_products / (all_norms * query_norm)

    results = [
        (ids[i], float(similarities[i]))
        for i in range(len(ids))
        if ids[i] != query_anime_id
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def get_recommendations(
    anime_name: str,
    conn: pyodbc.Connection,
    top_n: int = 10,
) -> tuple[str | None, pd.DataFrame | None]:
    """
    Retorna (titulo_encontrado, DataFrame com recomendações) ou (None, None).
    """
    matches = get_anime_by_name(conn, anime_name)
    if matches.empty:
        return None, None

    # Usa o anime de maior popularidade entre os matches
    query_anime = matches.sort_values("popularidade", ascending=False).iloc[0]
    query_id = int(query_anime["id"])
    found_title = query_anime["titulo"]

    animes_df = get_all_animes(conn)
    anime_tags_df = get_all_anime_tags_bulk(conn)

    matrix = build_feature_matrix(animes_df, anime_tags_df)
    similar = compute_similarity(matrix, query_id, top_n=top_n)

    if not similar:
        return found_title, pd.DataFrame()

    rec_ids = [s[0] for s in similar]
    scores = {s[0]: s[1] for s in similar}

    recs_df = animes_df[animes_df["id"].isin(rec_ids)].copy()
    recs_df["similaridade"] = recs_df["id"].map(scores)
    recs_df["similaridade_pct"] = (recs_df["similaridade"] * 100).round(1).astype(str) + "%"
    recs_df = recs_df.sort_values("similaridade", ascending=False)

    return found_title, recs_df[["titulo", "titulo_original", "nota", "popularidade",
                                  "generos", "estudio", "capa_url", "similaridade_pct"]]
