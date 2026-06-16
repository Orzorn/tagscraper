import requests
from datetime import datetime

MISSKEY_FAMILY = {"misskey", "calckey", "firefish", "iceshrimp", "sharkey", "catodon", "foundkey", "cherrypick"}


def _parse_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return str(int(dt.timestamp()))
    except Exception:
        return ""


def detect_software(instance):
    try:
        resp = requests.get(f"https://{instance}/.well-known/nodeinfo", timeout=10)
        resp.raise_for_status()
        links = resp.json().get("links", [])
        if not links:
            return None
        link = next((l for l in links if "2.1" in l["rel"]), links[0])
        resp2 = requests.get(link["href"], timeout=10)
        resp2.raise_for_status()
        return resp2.json().get("software", {}).get("name", "").lower()
    except Exception:
        return None


def fetch_tag_posts(instance, tag, limit=40, max_id=None):
    url = f"https://{instance}/api/v1/timelines/tag/{tag}"
    params = {"limit": limit}
    if max_id:
        params["max_id"] = max_id
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_tag_posts_misskey(instance, tag, limit=40, until_id=None):
    url = f"https://{instance}/api/notes/search-by-tag"
    body = {"tag": tag, "limit": limit, "withFiles": True}
    if until_id:
        body["untilId"] = until_id
    resp = requests.post(url, json=body, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _extract_images_mastodon(post):
    return (
        [{"url": a["url"], "is_image": a["type"] == "image"} for a in post.get("media_attachments", [])],
        {t["name"].lower() for t in post.get("tags", [])},
        post.get("url"),
        _parse_date(post.get("created_at", "")),
    )


def _extract_images_misskey(post):
    return (
        [{"url": f["url"], "is_image": f.get("type", "").startswith("image/")} for f in post.get("files", [])],
        {t.lower() for t in post.get("tags", [])},
        post.get("url") or post.get("uri"),
        _parse_date(post.get("createdAt", "")),
    )


def scrape_images(instance, tags, negative_tags=None):
    negative_tags = {t.lower() for t in (negative_tags or [])}
    seen_ids = set()

    software = detect_software(instance)
    use_misskey = software in MISSKEY_FAMILY

    for tag in tags:
        cursor = None

        while True:
            if use_misskey:
                batch = fetch_tag_posts_misskey(instance, tag, until_id=cursor)
            else:
                batch = fetch_tag_posts(instance, tag, max_id=cursor)

            if not batch:
                break

            for post in batch:
                if post["id"] in seen_ids:
                    continue
                seen_ids.add(post["id"])

                if use_misskey:
                    attachments, post_tags, post_url, post_date = _extract_images_misskey(post)
                else:
                    attachments, post_tags, post_url, post_date = _extract_images_mastodon(post)

                if post_tags & negative_tags:
                    continue

                for a in attachments:
                    if a["is_image"]:
                        yield {
                            "url": a["url"],
                            "post_url": post_url,
                            "instance": instance,
                            "tag": tag,
                            "tags": post_tags,
                            "date": post_date,
                        }

            cursor = batch[-1]["id"]
