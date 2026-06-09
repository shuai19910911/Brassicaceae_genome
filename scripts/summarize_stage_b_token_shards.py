#!/usr/bin/env python3
"""Summarize generated Stage B token shards."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-dir", default="stage_b_token_shards")
    parser.add_argument("--out", default="stage_b_token_shards/manifest.tsv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    shard_dir = Path(args.shard_dir)
    rows = []
    totals = {"train_windows": 0, "validation_windows": 0, "test_windows": 0, "train_tokens": 0, "validation_tokens": 0, "test_tokens": 0}
    for path in sorted(shard_dir.glob("shard_*.stats.json")):
        data = json.loads(path.read_text())
        for key in totals:
            totals[key] += int(data.get(key, 0))
        for split in ["train", "validation", "test"]:
            bin_path = shard_dir / f"{split}_{int(data['shard_index']):05d}.bin"
            idx_path = shard_dir / f"{split}_{int(data['shard_index']):05d}.idx.tsv"
            rows.append(
                {
                    "split": split,
                    "shard_index": data["shard_index"],
                    "bin_path": bin_path.name,
                    "idx_path": idx_path.name,
                    "bin_bytes": bin_path.stat().st_size if bin_path.exists() else 0,
                    "idx_bytes": idx_path.stat().st_size if idx_path.exists() else 0,
                    "windows": data.get(f"{split}_windows", 0),
                    "tokens": data.get(f"{split}_tokens", 0),
                }
            )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["split", "shard_index", "bin_path", "idx_path", "bin_bytes", "idx_bytes", "windows", "tokens"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = out.with_name("summary.json")
    summary.write_text(json.dumps(totals, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out}")
    print(json.dumps(totals, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
