#!/usr/bin/env python3
"""Create one self-contained Stage B transfer folder using hardlinks where possible."""

from __future__ import annotations

import argparse
import csv
import os
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data_manifests/brassicaceae_assemblies.tsv")
    parser.add_argument("--splits", default="data_manifests/brassicaceae_splits.tsv")
    parser.add_argument("--bundle-dir", default="training_server_transfer/stage_b_bundle")
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

    file_groups = {
        "data_manifests": [
            "brassicaceae_assemblies.tsv",
            "brassicaceae_splits.tsv",
            "region_candidates_4k_summary.tsv",
            "region_candidates_4k_by_assembly.tsv",
            "region_candidates_8k_summary.tsv",
            "region_candidates_8k_by_assembly.tsv",
            "region_candidates_16k_summary.tsv",
            "region_candidates_16k_by_assembly.tsv",
            "stage_b_sampling_plan.tsv",
        ],
        "configs": ["stage_b_data.yaml"],
        "sequence_index": ["contigs.tsv", "assembly_qc.tsv", "fasta_checksums.tsv"],
        "annotation_index": ["annotation_feature_summary.tsv", "annotation_coordinate_qc.tsv"],
        "sampling_index": [
            "region_candidates_4k.shard00.tsv",
            "region_candidates_4k.shard01.tsv",
            "region_candidates_4k.shard02.tsv",
            "region_candidates_8k.shard00.tsv",
            "region_candidates_8k.shard01.tsv",
            "region_candidates_8k.shard02.tsv",
            "region_candidates_16k.shard00.tsv",
            "region_candidates_16k.shard01.tsv",
            "region_candidates_16k.shard02.tsv",
        ],
        "scripts": [
            "build_manifest.py",
            "fasta_qc.py",
            "parse_annotations.py",
            "merge_qc_shards.py",
            "recompute_fasta_qc.py",
            "build_splits.py",
            "summarize_annotation_qc.py",
            "build_region_candidates.py",
            "summarize_region_candidates.py",
            "build_stage_b_sampling_plan.py",
            "create_stage_b_transfer_bundle.py",
        ],
    }

    missing: list[str] = []
    for dirname, names in file_groups.items():
        for name in names:
            src = Path(dirname) / name
            if not src.exists():
                missing.append(str(src))
                continue
            link_or_copy(src, bundle / dirname / name)

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
        missing_path = bundle / "MISSING_FILES.txt"
        missing_path.write_text("\n".join(missing) + "\n")
        raise SystemExit(f"missing required files, see {missing_path}")

    print(f"wrote bundle {bundle}")
    print(f"raw_genomes={len(raw_rows)}")
    print(f"files={sum(1 for p in bundle.rglob('*') if p.is_file())}")


if __name__ == "__main__":
    main()
