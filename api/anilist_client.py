import time
import requests
from api.queries import FETCH_TOP_ANIMES_QUERY

ANILIST_URL = "https://graphql.anilist.co"
MAX_RETRIES = 5


def execute_query(query: str, variables: dict) -> dict:
    for attempt in range(MAX_RETRIES):
        response = requests.post(
            ANILIST_URL,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"  Rate limit atingido. Aguardando {retry_after}s...")
            time.sleep(retry_after)
            continue

        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise RuntimeError(f"Erro GraphQL: {data['errors']}")

        return data

    raise RuntimeError(f"Falha após {MAX_RETRIES} tentativas.")


def fetch_page(page: int, per_page: int = 50) -> dict:
    data = execute_query(FETCH_TOP_ANIMES_QUERY, {"page": page, "perPage": per_page})
    return data["data"]["Page"]
