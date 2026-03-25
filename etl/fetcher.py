import math
import time
from api.anilist_client import fetch_page


def fetch_all_animes(total: int = 500, per_page: int = 50) -> list[dict]:
    num_pages = math.ceil(total / per_page)
    all_media = []

    for page in range(1, num_pages + 1):
        print(f"  Buscando página {page}/{num_pages}...")
        page_data = fetch_page(page, per_page)
        media = page_data.get("media") or []
        all_media.extend(media)
        print(f"  > {len(all_media)} animes acumulados")

        if not page_data.get("pageInfo", {}).get("hasNextPage", False):
            print("  Sem mais páginas disponíveis.")
            break

        if page < num_pages:
            time.sleep(0.7)

    return all_media[:total]
