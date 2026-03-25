from database.connection import get_connection
from database.repository import upsert_anime, upsert_tag, upsert_anime_tag
from etl.transformer import transform_anime, transform_tags, transform_anime_tags

BATCH_SIZE = 50


def load_all(raw_animes: list[dict]) -> None:
    conn = get_connection()
    try:
        for i, raw in enumerate(raw_animes):
            upsert_anime(conn, transform_anime(raw))
            for tag in transform_tags(raw):
                upsert_tag(conn, tag)
            for at in transform_anime_tags(raw):
                upsert_anime_tag(conn, at)

            if (i + 1) % BATCH_SIZE == 0:
                conn.commit()
                print(f"  Commit: {i + 1}/{len(raw_animes)} registros salvos")

        conn.commit()
        print(f"\nOK Carregados {len(raw_animes)} animes no banco de dados.")
    finally:
        conn.close()
