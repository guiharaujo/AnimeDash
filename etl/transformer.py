import html
import re


def _clean_description(text: str | None) -> str | None:
    if not text:
        return None
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip() or None


def transform_anime(raw: dict) -> dict:
    studios = raw.get("studios") or {}
    nodes = studios.get("nodes") or []
    estudio = nodes[0]["name"] if nodes else None

    cover = raw.get("coverImage") or {}
    capa_url = cover.get("large")

    genres = raw.get("genres") or []
    generos = ", ".join(genres) if genres else None

    return {
        "id":              raw["id"],
        "titulo":          (raw.get("title") or {}).get("romaji") or str(raw["id"]),
        "titulo_original": (raw.get("title") or {}).get("native"),
        "generos":         generos,
        "nota":            raw.get("meanScore"),
        "popularidade":    raw.get("popularity"),
        "episodios":       raw.get("episodes"),
        "status":          raw.get("status"),
        "temporada":       raw.get("season"),
        "ano":             raw.get("seasonYear"),
        "estudio":         estudio,
        "descricao":       _clean_description(raw.get("description")),
        "capa_url":        capa_url,
    }


def transform_tags(raw: dict) -> list[dict]:
    tags = []
    seen = set()
    for tag in raw.get("tags") or []:
        tag_id = tag.get("id")
        if tag_id is None or tag_id in seen:
            continue
        seen.add(tag_id)
        tags.append({
            "id":       tag_id,
            "nome":     tag.get("name") or "",
            "descricao": tag.get("description"),
        })
    return tags


def transform_anime_tags(raw: dict) -> list[dict]:
    anime_id = raw["id"]
    relations = []
    for tag in raw.get("tags") or []:
        tag_id = tag.get("id")
        if tag_id is None:
            continue
        relations.append({
            "id_anime": anime_id,
            "id_tag":   tag_id,
            "rank":     tag.get("rank"),
        })
    return relations
