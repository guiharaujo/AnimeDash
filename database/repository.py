import pyodbc
import pandas as pd


# ---------------------------------------------------------------------------
# Upserts
# ---------------------------------------------------------------------------

def upsert_anime(conn: pyodbc.Connection, anime: dict) -> None:
    sql = """
    MERGE INTO Animes AS target
    USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS source
        (id, titulo, titulo_original, generos, nota, popularidade, episodios,
         status, temporada, ano, estudio, descricao, capa_url)
    ON target.id = source.id
    WHEN MATCHED THEN UPDATE SET
        titulo          = source.titulo,
        titulo_original = source.titulo_original,
        generos         = source.generos,
        nota            = source.nota,
        popularidade    = source.popularidade,
        episodios       = source.episodios,
        status          = source.status,
        temporada       = source.temporada,
        ano             = source.ano,
        estudio         = source.estudio,
        descricao       = source.descricao,
        capa_url        = source.capa_url
    WHEN NOT MATCHED THEN INSERT
        (id, titulo, titulo_original, generos, nota, popularidade, episodios,
         status, temporada, ano, estudio, descricao, capa_url)
    VALUES
        (source.id, source.titulo, source.titulo_original, source.generos,
         source.nota, source.popularidade, source.episodios, source.status,
         source.temporada, source.ano, source.estudio, source.descricao,
         source.capa_url);
    """
    conn.execute(sql, (
        anime["id"], anime["titulo"], anime["titulo_original"],
        anime["generos"], anime["nota"], anime["popularidade"],
        anime["episodios"], anime["status"], anime["temporada"],
        anime["ano"], anime["estudio"], anime["descricao"], anime["capa_url"],
    ))


def upsert_tag(conn: pyodbc.Connection, tag: dict) -> None:
    sql = """
    MERGE INTO Tags AS target
    USING (VALUES (?, ?, ?)) AS source (id, nome, descricao)
    ON target.id = source.id
    WHEN MATCHED THEN UPDATE SET
        nome      = source.nome,
        descricao = source.descricao
    WHEN NOT MATCHED THEN INSERT (id, nome, descricao)
    VALUES (source.id, source.nome, source.descricao);
    """
    conn.execute(sql, (tag["id"], tag["nome"], tag["descricao"]))


def upsert_anime_tag(conn: pyodbc.Connection, anime_tag: dict) -> None:
    sql = """
    MERGE INTO Anime_Tags AS target
    USING (VALUES (?, ?, ?)) AS source (id_anime, id_tag, rank)
    ON target.id_anime = source.id_anime AND target.id_tag = source.id_tag
    WHEN MATCHED THEN UPDATE SET rank = source.rank
    WHEN NOT MATCHED THEN INSERT (id_anime, id_tag, rank)
    VALUES (source.id_anime, source.id_tag, source.rank);
    """
    conn.execute(sql, (anime_tag["id_anime"], anime_tag["id_tag"], anime_tag["rank"]))


# ---------------------------------------------------------------------------
# Selects
# ---------------------------------------------------------------------------

def get_all_animes(conn: pyodbc.Connection) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM Animes ORDER BY popularidade DESC", conn)


def get_anime_by_name(conn: pyodbc.Connection, name: str) -> pd.DataFrame:
    sql = """
    SELECT * FROM Animes
    WHERE titulo LIKE ? OR titulo_original LIKE ?
    ORDER BY popularidade DESC
    """
    pattern = f"%{name}%"
    return pd.read_sql(sql, conn, params=(pattern, pattern))


def get_all_anime_tags_bulk(conn: pyodbc.Connection) -> pd.DataFrame:
    sql = """
    SELECT at.id_anime, at.id_tag, at.rank, t.nome
    FROM Anime_Tags at
    JOIN Tags t ON at.id_tag = t.id
    """
    return pd.read_sql(sql, conn)


def get_stats(conn: pyodbc.Connection) -> dict:
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Animes")
    total_animes = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(nota) FROM Animes WHERE nota IS NOT NULL")
    avg_score = cursor.fetchone()[0] or 0.0

    # Top genre: explode comma-separated generos and count
    cursor.execute("""
        SELECT TOP 1 value AS genre, COUNT(*) AS cnt
        FROM Animes
        CROSS APPLY STRING_SPLIT(generos, ',')
        WHERE generos IS NOT NULL AND generos != ''
        GROUP BY value
        ORDER BY cnt DESC
    """)
    row = cursor.fetchone()
    top_genre = row[0].strip() if row else "N/A"

    # Top studio
    cursor.execute("""
        SELECT TOP 1 estudio, COUNT(*) AS cnt
        FROM Animes
        WHERE estudio IS NOT NULL AND estudio != ''
        GROUP BY estudio
        ORDER BY cnt DESC
    """)
    row = cursor.fetchone()
    top_studio = row[0] if row else "N/A"

    cursor.execute("SELECT COUNT(*) FROM Tags")
    total_tags = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Animes WHERE status = 'RELEASING'")
    animes_releasing = cursor.fetchone()[0]

    return {
        "total_animes": total_animes,
        "avg_score": round(float(avg_score), 1),
        "top_genre": top_genre,
        "top_studio": top_studio,
        "total_tags": total_tags,
        "animes_releasing": animes_releasing,
    }
