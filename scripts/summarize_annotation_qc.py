#!/usr/bin/env python3
"""Stream annotation shards to summarize features and coordinate validity."""

from __future__ import annotations

import argparse
import csv
import glob
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contigs", default="sequence_index/contigs.tsv")
    parser.add_argument("--annotation-dir", default="annotation_index")
    parser.add_argument("--out-dir", default="annotation_index")
    return parser.parse_args()


def load_contig_lengths(path: Path) -> dict[str, int]:
    lengths: dict[str, int] = {}
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            lengths[row["standard_seq_id"]] = int(row["length"])
    return lengths


def stream_feature_files(pattern: str):
    for path in sorted(glob.glob(pattern)):
        with open(path) as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                yield Path(path).name, row


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    contig_lengths = load_contig_lengths(Path(args.contigs))
    feature_counts: dict[tuple[str, str], int] = defaultdict(int)
    invalid_counts: dict[str, int] = defaultdict(int)
    total_rows = 0

    patterns = [
        str(Path(args.annotation_dir) / "features.shard*.tsv"),
        str(Path(args.annotation_dir) / "introns.shard*.tsv"),
    ]
    for pattern in patterns:
        for shard_name, row in stream_feature_files(pattern):
            total_rows += 1
            assembly_id = row["assembly_id"]
            feature = row["feature"]
            feature_counts[(assembly_id, feature)] += 1
            try:
                start0 = int(row["start0"])
                end = int(row["end"])
            except ValueError:
                invalid_counts[assembly_id] += 1
                continue
            seq_len = contig_lengths.get(row["standard_seq_id"])
            if seq_len is None or start0 < 0 or end <= start0 or end > seq_len:
                invalid_counts[assembly_id] += 1

    summary_path = out_dir / "annotation_feature_summary.tsv"
    with summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["assembly_id", "feature", "count"], delimiter="\t")
        writer.writeheader()
        for (assembly_id, feature), count in sorted(feature_counts.items()):
            writer.writerow({"assembly_id": assembly_id, "feature": feature, "count": count})

    invalid_path = out_dir / "annotation_coordinate_qc.tsv"
    assemblies = sorted({assembly_id for assembly_id, _ in feature_counts} | set(invalid_counts))
    with invalid_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["assembly_id", "feature_rows", "invalid_coordinate_rows", "invalid_fraction"],
            delimiter="\t",
        )
        writer.writeheader()
        for assembly_id in assemblies:
            rows = sum(count for (aid, _), count in feature_counts.items() if aid == assembly_id)
            invalid = invalid_counts[assembly_id]
            writer.writerow(
                {
                    "assembly_id": assembly_id,
                    "feature_rows": rows,
                    "invalid_coordinate_rows": invalid,
                    "invalid_fraction": f"{invalid / rows:.8f}" if rows else "0.00000000",
                }
            )
    print(f"wrote {summary_path}")
    print(f"wrote {invalid_path}")
    print(f"streamed_rows={total_rows}")


if __name__ == "__main__":
    main()

