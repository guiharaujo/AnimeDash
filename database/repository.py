import sqlite3
import pandas as pd


def _df(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return pd.DataFrame.from_records(cur.fetchall(), columns=cols)


def upsert_anime(conn, anime: dict) -> None:
    conn.execute("""
        INSERT OR REPLACE INTO Animes
        (id, titulo, titulo_original, generos, nota, popularidade, episodios,
         status, temporada, ano, estudio, descricao, capa_url)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        anime["id"], anime["titulo"], anime["titulo_original"], anime["generos"],
        anime["nota"], anime["popularidade"], anime["episodios"], anime["status"],
        anime["temporada"], anime["ano"], anime["estudio"], anime["descricao"], anime["capa_url"],
    ))


def upsert_tag(conn, tag: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO Tags (id, nome, descricao) VALUES (?,?,?)",
        (tag["id"], tag["nome"], tag["descricao"])
    )


def upsert_anime_tag(conn, at: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO Anime_Tags (id_anime, id_tag, rank) VALUES (?,?,?)",
        (at["id_anime"], at["id_tag"], at["rank"])
    )


def get_all_animes(conn) -> pd.DataFrame:
    return _df(conn, "SELECT * FROM Animes ORDER BY popularidade DESC")


def get_anime_by_name(conn, name: str) -> pd.DataFrame:
    p = f"%{name}%"
    return _df(conn,
        "SELECT * FROM Animes WHERE titulo LIKE ? OR titulo_original LIKE ? ORDER BY popularidade DESC",
        (p, p))


def get_all_anime_tags_bulk(conn) -> pd.DataFrame:
    return _df(conn, """
        SELECT at.id_anime, at.id_tag, at.rank, t.nome
        FROM Anime_Tags at JOIN Tags t ON at.id_tag = t.id
    """)


def get_stats(conn) -> dict:
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Animes")
    total = cur.fetchone()[0]

    cur.execute("SELECT AVG(nota) FROM Animes WHERE nota IS NOT NULL")
    avg = cur.fetchone()[0] or 0.0

    # Top genre — feito em Python (SQLite nao tem STRING_SPLIT)
    cur.execute("SELECT generos FROM Animes WHERE generos IS NOT NULL AND generos != ''")
    from collections import Counter
    genre_counter = Counter()
    for (g,) in cur.fetchall():
        for genre in g.split(", "):
            genre_counter[genre.strip()] += 1
    top_genre = genre_counter.most_common(1)[0][0] if genre_counter else "N/A"

    cur.execute("""
        SELECT estudio, COUNT(*) cnt FROM Animes
        WHERE estudio IS NOT NULL AND estudio != ''
        GROUP BY estudio ORDER BY cnt DESC LIMIT 1
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
