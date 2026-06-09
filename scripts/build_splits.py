#!/usr/bin/env python3
"""Build deterministic assembly-level train/validation/test splits."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data_manifests/brassicaceae_assemblies.tsv")
    parser.add_argument("--assembly-qc", default="sequence_index/assembly_qc.tsv")
    parser.add_argument("--out", default="data_manifests/brassicaceae_splits.tsv")
    return parser.parse_args()


def stable_score(text: str) -> float:
    digest = hashlib.sha256(text.encode()).hexdigest()
    return int(digest[:16], 16) / float(16**16)


def assign_split(row: dict[str, str], genus_counts: dict[str, int]) -> str:
    genus = row["genus"]
    key = row.get("split_group") or row["assembly_id"]
    score = stable_score(key)

    if genus_counts[genus] <= 2:
        return "train" if score < 0.5 else "test"
    if genus_counts[genus] <= 5:
        if score < 0.70:
            return "train"
        return "validation" if score < 0.85 else "test"
    if score < 0.80:
        return "train"
    if score < 0.90:
        return "validation"
    return "test"


def main() -> None:
    args = parse_args()
    with Path(args.manifest).open() as handle:
        manifest_rows = [row for row in csv.DictReader(handle, delimiter="\t")]
    with Path(args.assembly_qc).open() as handle:
        qc_rows = {row["assembly_id"]: row for row in csv.DictReader(handle, delimiter="\t")}

    eligible = [
        row
        for row in manifest_rows
        if row.get("train_eligible") == "1"
        and qc_rows.get(row["assembly_id"], {}).get("qc_status") == "pass"
        and int(qc_rows.get(row["assembly_id"], {}).get("pass_bp", "0")) > 0
    ]
    genus_counts: dict[str, int] = defaultdict(int)
    for row in eligible:
        genus_counts[row["genus"]] += 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "assembly_id",
        "accession",
        "species",
        "genus",
        "split",
        "split_group",
        "pass_contigs",
        "pass_bp",
        "total_bp",
    ]
    split_counts: dict[str, int] = defaultdict(int)
    genus_split_counts: dict[tuple[str, str], int] = defaultdict(int)
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in sorted(eligible, key=lambda r: (r["genus"], r["assembly_id"])):
            split = assign_split(row, genus_counts)
            qc = qc_rows[row["assembly_id"]]
            writer.writerow(
                {
                    "assembly_id": row["assembly_id"],
                    "accession": row["accession"],
                    "species": row["species"],
                    "genus": row["genus"],
                    "split": split,
                    "split_group": row["split_group"],
                    "pass_contigs": qc["pass_contigs"],
                    "pass_bp": qc["pass_bp"],
                    "total_bp": qc["total_bp"],
                }
            )
            split_counts[split] += 1
            genus_split_counts[(row["genus"], split)] += 1
    print(f"wrote {out}")
    print("split_counts", dict(sorted(split_counts.items())))
    for (genus, split), count in sorted(genus_split_counts.items()):
        print(f"genus_split\t{genus}\t{split}\t{count}")


if __name__ == "__main__":
    main()

