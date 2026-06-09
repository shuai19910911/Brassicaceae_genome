#!/usr/bin/env python3
"""Summarize sharded region candidate windows into small TSV reports."""

from __future__ import annotations

import argparse
import csv
import glob
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-glob", default="sampling_index/region_candidates_8k.shard*.tsv")
    parser.add_argument("--out-dir", default="data_manifests")
    parser.add_argument("--label", default="8k")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = sorted(glob.glob(args.candidate_glob))
    by_region: dict[str, int] = defaultdict(int)
    by_split: dict[str, int] = defaultdict(int)
    by_assembly: dict[tuple[str, str, str], int] = defaultdict(int)
    total = 0

    for path in paths:
        with open(path) as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                total += 1
                by_region[row["region"]] += 1
                by_split[row["split"]] += 1
                by_assembly[(row["assembly_id"], row["split"], row["region"])] += 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / f"region_candidates_{args.label}_summary.tsv"
    with summary_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["metric", "name", "count", "fraction"])
        for name, count in sorted(by_split.items()):
            writer.writerow(["split", name, count, f"{count / total:.8f}"])
        for name, count in sorted(by_region.items()):
            writer.writerow(["region", name, count, f"{count / total:.8f}"])
        writer.writerow(["total", "all", total, "1.00000000"])

    assembly_path = out_dir / f"region_candidates_{args.label}_by_assembly.tsv"
    with assembly_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["assembly_id", "split", "region", "count"])
        for (assembly_id, split, region), count in sorted(by_assembly.items()):
            writer.writerow([assembly_id, split, region, count])

    print(f"wrote {summary_path}")
    print(f"wrote {assembly_path}")
    print(f"candidate_files={len(paths)} total_candidates={total}")


if __name__ == "__main__":
    main()
