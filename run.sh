#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Mode:"
echo "  1) Scrape"
echo "  2) Groom library"
read -rp "Choice [1]: " mode_input
mode_input="${mode_input:-1}"

if [[ "$mode_input" == "2" ]]; then
    read -rp "Tags to remove (space-separated): " remove_tags_input
    read -rp "Image directory [scraped_images]: " output_dir
    output_dir="${output_dir:-scraped_images}"
    read -rp "Metadata directory [$output_dir/metadata]: " metadata_dir
    metadata_dir="${metadata_dir:-$output_dir/metadata}"
    read -rp "Dry run? (y/n) [y]: " dry_run_input
    dry_run_input="${dry_run_input:-y}"

    cmd=(python3 "$SCRIPT_DIR/main.py" groom --output "$output_dir" --metadata "$metadata_dir")
    [[ -n "$remove_tags_input" ]] && cmd+=(--tags $remove_tags_input)
    [[ "$dry_run_input" =~ ^[Yy] ]] && cmd+=(--dry-run)

    echo ""
    echo "Running: ${cmd[*]}"
    echo ""
    "${cmd[@]}"
    exit 0
fi

read -rp "Instance (e.g. mastodon.social): " instance
instance="${instance:-dill.burggit.moe}"

read -rp "Tags (space-separated): " tags_input
read -rp "Negative tags (space-separated, leave blank to skip): " neg_tags_input
read -rp "Max posts (leave blank for no limit): " max_posts_input

read -rp "Download images? (y/n): " download_input
if [[ "$download_input" =~ ^[Yy] ]]; then
    read -rp "Image output directory [scraped_images]: " output_dir
    output_dir="${output_dir:-scraped_images}"
    metadata_dir="$output_dir/metadata"
fi

cmd=(python3 "$SCRIPT_DIR/main.py" scrape "$instance")

[[ -n "$tags_input" ]] && cmd+=(--tags $tags_input)
[[ -n "$neg_tags_input" ]] && cmd+=(--not $neg_tags_input)
[[ -n "$max_posts_input" ]] && cmd+=(--max "$max_posts_input")

if [[ "$download_input" =~ ^[Yy] ]]; then
    cmd+=(--download --output "$output_dir" --metadata "$metadata_dir")
fi

echo ""
echo "Running: ${cmd[*]}"
echo ""
"${cmd[@]}"
