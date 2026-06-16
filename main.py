#!/usr/bin/env python3
import argparse
import json
import os
import sys
from scraper import scrape_images
from downloader import download_images

BLACKLIST_PATH = os.path.join(os.path.dirname(__file__), "blacklist.txt")
REPEAT_SEARCH = os.path.join(os.path.dirname(__file__), "includelist.txt")

def load_list(use_path):
    if not os.path.exists(use_path):
        return set()
    with open(use_path) as f:
        return {line.strip().lower() for line in f if line.strip() and not line.startswith("#")}


def groom(remove_tags, output_dir="scraped_images", metadata_dir="metadata", dry_run=False):
    remove_tags = {t.lower() for t in remove_tags} | load_list(BLACKLIST_PATH)
    print(f"remove tags: {remove_tags}")
    if not os.path.isdir(metadata_dir):
        print(f"Metadata directory not found: {metadata_dir}", file=sys.stderr)
        sys.exit(1)

    removed = 0
    for filename in os.listdir(metadata_dir):
        if not filename.endswith(".json"):
            continue
        meta_path = os.path.join(metadata_dir, filename)
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except Exception:
            continue

        entry_tags = {t.lower() for t in meta.get("tags", "").split()}
        if not (entry_tags & remove_tags):
            continue

        hash_val = meta.get("hash", os.path.splitext(filename)[0])
        ext = meta.get("ext", "")
        image_path = os.path.join(output_dir, f"{hash_val}.{ext}") if ext else None

        matched = sorted(entry_tags & remove_tags)
        if dry_run:
            print(f"[dry-run] would remove {hash_val}.{ext} (matched: {', '.join(matched)})")
        else:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
            os.remove(meta_path)
            print(f"Removed {hash_val}.{ext} (matched: {', '.join(matched)})")
        removed += 1

    label = "would remove" if dry_run else "removed"
    print(f"{label} {removed} entr{'y' if removed == 1 else 'ies'}.")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape images from a Mastodon instance by hashtag."
    )
    subparsers = parser.add_subparsers(dest="command")

    scrape_parser = subparsers.add_parser("scrape", help="Scrape and optionally download images")
    scrape_parser.add_argument("instance", help="Mastodon instance domain (e.g. mastodon.social)")
    scrape_parser.add_argument("--tags", nargs="+", metavar="TAG", help="Tags to search for (includelist always included")
    scrape_parser.add_argument("--not", nargs="+", metavar="TAG", dest="negative_tags", help="Exclude posts containing these tags")
    scrape_parser.add_argument("--max", type=int, metavar="N", dest="max_posts", help="Max number of posts to scrape")
    scrape_parser.add_argument("--download", action="store_true", help="Download images and generate metadata JSON files")
    scrape_parser.add_argument("--output", default="scraped_images", metavar="DIR", help="Directory to save images (default: scraped_images)")
    scrape_parser.add_argument("--metadata", default="metadata", metavar="DIR", help="Directory to save metadata JSON files (default: metadata)")

    groom_parser = subparsers.add_parser("groom", help="Remove library entries matching specified tags")
    groom_parser.add_argument("--tags", nargs="*", default=[], metavar="TAG", help="Remove entries containing any of these tags (blacklist always included)")
    groom_parser.add_argument("--output", default="scraped_images", metavar="DIR", help="Image directory (default: scraped_images)")
    groom_parser.add_argument("--metadata", default="metadata", metavar="DIR", help="Metadata directory (default: metadata)")
    groom_parser.add_argument("--dry-run", action="store_true", help="Preview removals without deleting anything")

    # Support legacy flat invocation (no subcommand) for backwards compatibility
    parser.add_argument("--tags", nargs="+", metavar="TAG", help=argparse.SUPPRESS)
    parser.add_argument("--not", nargs="+", metavar="TAG", dest="negative_tags", help=argparse.SUPPRESS)
    parser.add_argument("--max", type=int, metavar="N", dest="max_posts", help=argparse.SUPPRESS)
    parser.add_argument("--download", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--output", default="scraped_images", metavar="DIR", help=argparse.SUPPRESS)
    parser.add_argument("--metadata", default="metadata", metavar="DIR", help=argparse.SUPPRESS)

    args, extra = parser.parse_known_args()

    if args.command == "groom":
        groom(
            remove_tags=args.tags,
            output_dir=args.output,
            metadata_dir=args.metadata,
            dry_run=args.dry_run,
        )
        return

    # scrape subcommand or legacy flat invocation
    if args.command == "scrape":
        instance = args.instance
        tags = set(args.tags or []) | load_list(REPEAT_SEARCH)
        print(f"Tags: {tags}")
        negative_tags = set(args.negative_tags or []) | load_list(BLACKLIST_PATH)
        max_posts = args.max_posts
        download = args.download
        output = args.output
        metadata = args.metadata
    else:
        legacy_instance = extra[0] if extra else None
        if not legacy_instance or not args.tags:
            parser.print_help()
            sys.exit(1)
        instance = legacy_instance
        tags = set(args.tags or []) | load_list(REPEAT_SEARCH)
        negative_tags = set(args.negative_tags or []) | load_list(BLACKLIST_PATH)
        max_posts = args.max_posts
        download = args.download
        output = args.output
        metadata = args.metadata

    images = scrape_images(instance=instance, tags=tags, negative_tags=negative_tags)

    if download:
        try:
            download_images(images, output_dir=output, metadata_dir=metadata, max_new=max_posts)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        count = 0
        try:
            for img in images:
                print(img["url"])
                count += 1
                if max_posts and count >= max_posts:
                    break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if not count:
            print("No images found.")


if __name__ == "__main__":
    main()
