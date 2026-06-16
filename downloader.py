import hashlib
import io
import json
import os
from urllib.parse import urlparse

import requests
from PIL import Image

_EXT_FROM_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/avif": "avif",
}


def _get_extension(url, content_type=""):
    path = urlparse(url).path.split("?")[0]
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "jpeg":
        ext = "jpg"
    if ext in {"jpg", "png", "gif", "webp", "avif"}:
        return ext
    for mime, mapped in _EXT_FROM_CONTENT_TYPE.items():
        if mime in content_type:
            return mapped
    return ext or "jpg"


def download_images(images, output_dir="scraped_images", metadata_dir="metadata", max_new=None):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)

    existing = {os.path.splitext(e.name)[0] for e in os.scandir(output_dir) if e.is_file()}
    new_count = 0

    for img in images:
        if max_new is not None and new_count >= max_new:
            break

        url = img["url"]
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            continue

        data = resp.content
        hash_val = hashlib.md5(data).hexdigest()

        if hash_val in existing:
            continue

        ext = _get_extension(url, resp.headers.get("Content-Type", ""))

        with open(os.path.join(output_dir, f"{hash_val}.{ext}"), "wb") as f:
            f.write(data)

        try:
            with Image.open(io.BytesIO(data)) as pil_img:
                width, height = pil_img.size
        except Exception:
            width, height = 0, 0

        tags_str = " ".join(sorted(img.get("tags", set())))
        metadata = {
            "tags": tags_str,
            "width": width,
            "height": height,
            "date": img.get("date", ""),
            "source": img.get("post_url", ""),
            "hash": hash_val,
            "ext": ext,
        }

        with open(os.path.join(metadata_dir, f"{hash_val}.json"), "w") as f:
            json.dump(metadata, f, separators=(",", ":"))

        existing.add(hash_val)
        new_count += 1
        print(f"Saved {hash_val}.{ext}")
