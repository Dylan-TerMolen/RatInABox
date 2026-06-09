#!/usr/bin/env bash
RESULTS_DIR="$(dirname "$0")/../saved/results"

dirs=$(find "$RESULTS_DIR" -type d -name "*_results")
csv_count=$(find "$RESULTS_DIR" -type d -name "*_results" -exec find {} -maxdepth 1 -name "*.csv" \; | wc -l | tr -d ' ')

echo "This will delete $csv_count .csv file(s) from:"
while IFS= read -r dir; do
    echo "  - $(basename "$dir")"
done <<< "$dirs"
echo ""
read -r -p "Continue? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || exit 0

find "$RESULTS_DIR" -type d -name "*_results" -exec find {} -maxdepth 1 -name "*.csv" -delete \;
echo "Done."
