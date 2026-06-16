# TagScraper

A command-line tool for scraping and downloading images from Mastodon (and compatible) instances by hashtag. Supports both Mastodon-compatible instances and Misskey-family instances (Misskey, Calckey, Firefish, Sharkey, etc.).

## Features

- Scrape image URLs from one or more hashtags across any Mastodon or Misskey-family instance
- Download images locally, deduplicating by MD5 hash
- Save per-image metadata (tags, dimensions, source URL, date) as JSON sidecar files
- Exclude posts by tag (blacklist) or include tags on every run (includelist)
- Groom your local library by removing images that match unwanted tags

## Requirements

- Python 3.8+
- `requests`
- `Pillow`

Install dependencies:

```bash
pip install requests Pillow
```

## Usage

### Interactive mode

```bash
./run.sh
```

This is the suggested usage mode.
It prompts you through scraping or grooming step by step.

### Scrape

```bash
python main.py scrape <instance> [options]
```

| Option | Description |
|---|---|
| `--tags TAG [TAG ...]` | Hashtags to search (includelist is always added) |
| `--not TAG [TAG ...]` | Exclude posts containing any of these tags (blacklist is always added) |
| `--max N` | Stop after N images |
| `--download` | Download images instead of just printing URLs |
| `--output DIR` | Image output directory (default: `scraped_images`) |
| `--metadata DIR` | Metadata output directory (default: `scraped_images\metadata`) |

It should be noted that the scraper performs hashtag based matching, so that if an image has previously been downloaded, if you run the same scrape
command it will skip previously downloaded images that match the hash you have and proceed to the next available image to download.

**Examples:**

Print image URLs for `#photography` on mastodon.social:

```bash
python main.py scrape mastodon.social --tags photography
```

Download images for multiple tags, excluding certain content:

```bash
python main.py scrape mastodon.social --tags photography landscape --not nsfw --download
```

### Groom

Remove images and their metadata from a local library when they match unwanted tags:

```bash
python main.py groom [options]
```

| Option | Description |
|---|---|
| `--tags TAG [TAG ...]` | Remove entries matching any of these tags (blacklist is always added) |
| `--output DIR` | Image directory (default: `scraped_images`) |
| `--metadata DIR` | Metadata directory (default: `metadata`) |
| `--dry-run` | Preview what would be removed without deleting anything |

**Example:**

```bash
python main.py groom --tags unwanted_tag --dry-run
```

## Blacklist and Includelist

- **`blacklist.txt`** — one tag per line. Tags listed here are always excluded during scraping and always targeted during grooming, regardless of command-line flags.
- **`includelist.txt`** — one tag per line. Tags listed here are always added to every scrape run, regardless of `--tags`.

Lines beginning with `#` are treated as comments and ignored.

## Output structure

```
scraped_images/
    <md5hash>.<ext>
    ...
metadata/
    <md5hash>.json
    ...
```

Each metadata JSON file contains:

```json
{
  "tags": "tag1 tag2 tag3",
  "width": 1920,
  "height": 1080,
  "date": "1700000000",
  "source": "https://instance.example/posts/...",
  "hash": "abc123...",
  "ext": "jpg"
}
```

## License

This project is licensed under the GNU General Public License v2.0. See [LICENSE](LICENSE) for details.
