#!/usr/bin/env python3
"""Create a self-contained transfer folder containing all generated stages."""

from __future__ import annotations

import argparse
import csv
import glob
import os
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data_manifests/brassicaceae_assemblies.tsv")
    parser.add_argument("--splits", default="data_manifests/brassicaceae_splits.tsv")
    parser.add_argument("--bundle-dir", default="training_server_transfer/all_stages_bundle")
    return parser.parse_args()


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def read_split_ids(path: Path) -> set[str]:
    with path.open() as handle:
        return {row["assembly_id"] for row in csv.DictReader(handle, delimiter="\t")}


def copy_patterns(bundle: Path, patterns: list[str]) -> list[str]:
    missing = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if not matches:
            missing.append(pattern)
            continue
        for src_s in matches:
            src = Path(src_s)
            link_or_copy(src, bundle / src)
    return missing


def main() -> None:
    args = parse_args()
    bundle = Path(args.bundle_dir)
    bundle.mkdir(parents=True, exist_ok=True)
    split_ids = read_split_ids(Path(args.splits))

    raw_rows = []
    with Path(args.manifest).open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["assembly_id"] not in split_ids:
                continue
            src = Path(row["genome_path"])
            dst = bundle / "raw_genomes" / row["assembly_id"] / src.name
            link_or_copy(src, dst)
            raw_rows.append(
                {
                    "assembly_id": row["assembly_id"],
                    "source_genome_path": str(src),
                    "bundle_genome_path": str(dst.relative_to(bundle)),
                    "bytes": src.stat().st_size,
                }
            )

    patterns = [
        "README.md",
        "PROGRESS.md",
        "DIRECTORY_STRUCTURE.md",
        "TRANSFER_MANIFEST.md",
        "MODEL_STRUCTURE.md",
        "configs/*.yaml",
        "data_manifests/brassicaceae_assemblies.tsv",
        "data_manifests/brassicaceae_splits.tsv",
        "data_manifests/region_candidates_*_summary.tsv",
        "data_manifests/region_candidates_*_by_assembly.tsv",
        "data_manifests/stage_*_sampling_plan.tsv",
        "data_manifests/stage_*_token_shard_plan.tsv",
        "sequence_index/contigs.tsv",
        "sequence_index/assembly_qc.tsv",
        "sequence_index/fasta_checksums.tsv",
        "annotation_index/annotation_feature_summary.tsv",
        "annotation_index/annotation_coordinate_qc.tsv",
        "sampling_index/region_candidates_*.shard*.tsv",
        "scripts/*.py",
        "stage_*_token_shards/*.bin",
        "stage_*_token_shards/*.idx.tsv",
        "stage_*_token_shards/*.stats.json",
        "stage_*_token_shards/manifest.tsv",
        "stage_*_token_shards/summary.json",
    ]
    missing = copy_patterns(bundle, patterns)

    raw_manifest = bundle / "raw_genomes_manifest.tsv"
    with raw_manifest.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["assembly_id", "source_genome_path", "bundle_genome_path", "bytes"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(raw_rows)

    transfer_files = bundle / "TRANSFER_FILES.tsv"
    with transfer_files.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["relative_path", "bytes"])
        for path in sorted(p for p in bundle.rglob("*") if p.is_file()):
            writer.writerow([path.relative_to(bundle), path.stat().st_size])

    if missing:
        (bundle / "MISSING_PATTERNS.txt").write_text("\n".join(missing) + "\n")
    print(f"wrote bundle {bundle}")
    print(f"raw_genomes={len(raw_rows)}")
    print(f"files={sum(1 for p in bundle.rglob('*') if p.is_file())}")
    if missing:
        print(f"missing_patterns={len(missing)}")


if __name__ == "__main__":
    main()
