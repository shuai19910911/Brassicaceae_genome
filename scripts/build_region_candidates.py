#!/usr/bin/env python3
"""Build sharded 8K region-aware candidate windows for Stage B sampling."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


FEATURE_WEIGHT = {
    "cds": 5.0,
    "exon": 4.0,
    "five_prime_utr": 4.0,
    "three_prime_utr": 4.0,
    "intron": 2.0,
    "mrna": 1.5,
    "transcript": 1.5,
    "gene": 1.5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contigs", default="sequence_index/contigs.tsv")
    parser.add_argument("--splits", default="data_manifests/brassicaceae_splits.tsv")
    parser.add_argument("--annotation-dir", default="annotation_index")
    parser.add_argument("--out-dir", default="sampling_index")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--num-shards", type=int, default=3)
    parser.add_argument("--context-len", type=int, default=8192)
    parser.add_argument("--background-stride", type=int, default=65536)
    return parser.parse_args()


def load_splits(path: Path) -> dict[str, str]:
    with path.open() as handle:
        return {row["assembly_id"]: row["split"] for row in csv.DictReader(handle, delimiter="\t")}


def load_pass_contigs(path: Path, split_map: dict[str, str]) -> dict[str, dict[str, str | int | float]]:
    contigs: dict[str, dict[str, str | int | float]] = {}
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["assembly_id"] not in split_map or row["pass_qc"] != "1":
                continue
            contigs[row["standard_seq_id"]] = {
                "assembly_id": row["assembly_id"],
                "seq_id": row["seq_id"],
                "length": int(row["length"]),
                "gc_fraction": float(row["gc_fraction"]),
                "n_fraction": float(row["n_fraction"]),
                "split": split_map[row["assembly_id"]],
            }
    return contigs


def window_start(start0: int, end: int, contig_len: int, context_len: int) -> int:
    center = (start0 + end) // 2
    start = center - context_len // 2
    if start < 0:
        start = 0
    if start + context_len > contig_len:
        start = max(0, contig_len - context_len)
    return start


def add_candidate(
    candidates: dict[tuple[str, int, int], dict[str, str | int | float]],
    contig: dict[str, str | int | float],
    standard_seq_id: str,
    start: int,
    context_len: int,
    region: str,
    weight: float,
) -> None:
    key = (standard_seq_id, start, context_len)
    existing = candidates.get(key)
    if existing is not None and float(existing["region_weight"]) >= weight:
        return
    candidates[key] = {
        "assembly_id": contig["assembly_id"],
        "seq_id": contig["seq_id"],
        "standard_seq_id": standard_seq_id,
        "start0": start,
        "end": start + context_len,
        "context_len": context_len,
        "region": region,
        "region_weight": f"{weight:.3f}",
        "split": contig["split"],
        "gc_fraction": f"{float(contig['gc_fraction']):.6f}",
        "n_fraction": f"{float(contig['n_fraction']):.6f}",
    }


def stream_feature_rows(annotation_dir: Path, shard_index: int):
    patterns = [
        annotation_dir / f"features.shard{shard_index:02d}.tsv",
        annotation_dir / f"introns.shard{shard_index:02d}.tsv",
    ]
    for path in patterns:
        if not path.exists():
            continue
        with path.open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                yield row


def main() -> None:
    args = parse_args()
    split_map = load_splits(Path(args.splits))
    pass_contigs = load_pass_contigs(Path(args.contigs), split_map)
    candidates: dict[tuple[str, int, int], dict[str, str | int | float]] = {}

    for row in stream_feature_rows(Path(args.annotation_dir), args.shard_index):
        feature = row["feature"]
        if feature not in FEATURE_WEIGHT:
            continue
        contig = pass_contigs.get(row["standard_seq_id"])
        if contig is None:
            continue
        try:
            start0 = int(row["start0"])
            end = int(row["end"])
        except ValueError:
            continue
        contig_len = int(contig["length"])
        if start0 < 0 or end <= start0 or end > contig_len or contig_len < args.context_len:
            continue
        start = window_start(start0, end, contig_len, args.context_len)
        add_candidate(candidates, contig, row["standard_seq_id"], start, args.context_len, feature, FEATURE_WEIGHT[feature])

    # Sparse high-quality background tiling for every pass contig.
    for standard_seq_id, contig in pass_contigs.items():
        contig_len = int(contig["length"])
        if contig_len < args.context_len:
            continue
        digest = hashlib.sha256(str(contig["assembly_id"]).encode()).hexdigest()
        if int(digest[:8], 16) % args.num_shards != args.shard_index:
            continue
        for start in range(0, max(1, contig_len - args.context_len + 1), args.background_stride):
            add_candidate(candidates, contig, standard_seq_id, start, args.context_len, "background", 0.25)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"region_candidates_8k.shard{args.shard_index:02d}.tsv"
    fields = [
        "assembly_id",
        "seq_id",
        "standard_seq_id",
        "start0",
        "end",
        "context_len",
        "region",
        "region_weight",
        "split",
        "gc_fraction",
        "n_fraction",
    ]
    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for record in sorted(candidates.values(), key=lambda r: (r["assembly_id"], r["standard_seq_id"], int(r["start0"]))):
            writer.writerow(record)
    print(f"wrote {out_path}")
    print(f"candidates={len(candidates)}")


if __name__ == "__main__":
    main()
