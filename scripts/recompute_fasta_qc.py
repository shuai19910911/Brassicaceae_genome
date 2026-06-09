#!/usr/bin/env python3
"""Recompute contig pass flags and assembly QC from an existing contig TSV."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contigs", default="sequence_index/contigs.tsv")
    parser.add_argument("--out-contigs", default="sequence_index/contigs.tsv")
    parser.add_argument("--out-assembly-qc", default="sequence_index/assembly_qc.tsv")
    parser.add_argument("--min-contig-len", type=int, default=10_000)
    parser.add_argument("--max-n-fraction", type=float, default=0.10)
    return parser.parse_args()


def pass_qc(row: dict[str, str], min_len: int, max_n_fraction: float) -> str:
    return str(
        int(
            int(row["length"]) >= min_len
            and float(row["n_fraction"]) <= max_n_fraction
            and row["seq_class"] == "nuclear_or_unknown"
        )
    )


def main() -> None:
    args = parse_args()
    contig_path = Path(args.contigs)
    tmp_contigs = Path(str(args.out_contigs) + ".tmp")
    assembly_stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"contigs": 0, "pass_contigs": 0, "total_bp": 0, "pass_bp": 0}
    )

    with contig_path.open() as inp, tmp_contigs.open("w", newline="") as out:
        reader = csv.DictReader(inp, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("missing contig header")
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames, delimiter="\t")
        writer.writeheader()
        for row in reader:
            row["pass_qc"] = pass_qc(row, args.min_contig_len, args.max_n_fraction)
            length = int(row["length"])
            stats = assembly_stats[row["assembly_id"]]
            stats["contigs"] += 1
            stats["total_bp"] += length
            if row["pass_qc"] == "1":
                stats["pass_contigs"] += 1
                stats["pass_bp"] += length
            writer.writerow(row)

    tmp_assembly = Path(str(args.out_assembly_qc) + ".tmp")
    with tmp_assembly.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["assembly_id", "contigs", "pass_contigs", "total_bp", "pass_bp", "qc_status"],
            delimiter="\t",
        )
        writer.writeheader()
        for assembly_id, stats in sorted(assembly_stats.items()):
            writer.writerow(
                {
                    "assembly_id": assembly_id,
                    **stats,
                    "qc_status": "pass" if stats["pass_bp"] > 0 else "fail",
                }
            )

    tmp_contigs.replace(args.out_contigs)
    tmp_assembly.replace(args.out_assembly_qc)
    print(f"wrote {args.out_contigs}")
    print(f"wrote {args.out_assembly_qc}")
    print(f"assemblies={len(assembly_stats)} pass={sum(1 for s in assembly_stats.values() if s['pass_bp'] > 0)}")


if __name__ == "__main__":
    main()

