#!/usr/bin/env python3
"""Merge small FASTA QC shard TSVs without duplicating large annotation tables."""

from __future__ import annotations

import argparse
import glob
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-dir", default="sequence_index")
    return parser.parse_args()


def merge(pattern: str, out_path: Path) -> tuple[int, int]:
    paths = [Path(path) for path in sorted(glob.glob(pattern))]
    if not paths:
        raise FileNotFoundError(f"no shards matched {pattern}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total_rows = 0
    with out_path.open("w") as out:
        for i, path in enumerate(paths):
            with path.open() as handle:
                header = handle.readline()
                if i == 0:
                    out.write(header)
                for line in handle:
                    out.write(line)
                    total_rows += 1
    return len(paths), total_rows


def main() -> None:
    args = parse_args()
    seq_dir = Path(args.sequence_dir)
    jobs = [
        ("contigs.shard*.tsv", "contigs.tsv"),
        ("assembly_qc.shard*.tsv", "assembly_qc.tsv"),
        ("fasta_checksums.shard*.tsv", "fasta_checksums.tsv"),
    ]
    for pattern, out_name in jobs:
        shard_count, row_count = merge(str(seq_dir / pattern), seq_dir / out_name)
        print(f"wrote {seq_dir / out_name} shards={shard_count} rows={row_count}")


if __name__ == "__main__":
    main()

