#!/usr/bin/env python3
"""Build the Brassicaceae assembly manifest from local plantDB downloads."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


BRASSICACEAE_GENERA = {
    "Arabidopsis",
    "Arabis",
    "Brassica",
    "Camelina",
    "Capsella",
    "Cardamine",
    "Noccaea",
    "Sinapis",
    "Thlaspi",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--genome-root",
        default="/home/user/zhangzhishuai/data/plantDB/genome",
        help="Root directory containing per-assembly plantDB downloads.",
    )
    parser.add_argument(
        "--out",
        default="data_manifests/brassicaceae_assemblies.tsv",
        help="Output manifest TSV path.",
    )
    return parser.parse_args()


def accession_from_name(name: str) -> str:
    match = re.search(r"(GC[AF]_\d+\.\d+)", name)
    return match.group(1) if match else ""


def species_from_name(name: str) -> str:
    parts = name.split("_")
    if len(parts) < 2:
        return name
    stop = len(parts)
    for i, part in enumerate(parts):
        if re.match(r"GC[AF]$", part):
            stop = i
            break
    return "_".join(parts[:stop])


def read_source_metadata(assembly_dir: Path) -> dict[str, str]:
    path = assembly_dir / "metadata" / "source_metadata.json"
    if not path.exists():
        return {}
    try:
        with path.open() as handle:
            data = json.load(handle)
        return {str(k): str(v) for k, v in data.items() if v is not None}
    except Exception:
        return {}


def first_or_empty(paths: list[Path]) -> str:
    if not paths:
        return ""
    return str(sorted(paths)[0])


def main() -> None:
    args = parse_args()
    root = Path(args.genome_root)
    rows: list[dict[str, str | int]] = []

    for assembly_dir in sorted(root.iterdir()):
        if not assembly_dir.is_dir():
            continue
        genus = assembly_dir.name.split("_", 1)[0]
        if genus not in BRASSICACEAE_GENERA:
            continue

        genome_paths = (
            list((assembly_dir / "genome").glob("*.fna.gz"))
            + list((assembly_dir / "genome").glob("*.fa.gz"))
            + list((assembly_dir / "genome").glob("*.fasta.gz"))
            + list((assembly_dir / "genome").glob("*.fna"))
            + list((assembly_dir / "genome").glob("*.fa"))
            + list((assembly_dir / "genome").glob("*.fasta"))
        )
        gff_paths = (
            list((assembly_dir / "annotation").glob("*.gff.gz"))
            + list((assembly_dir / "annotation").glob("*.gff3.gz"))
            + list((assembly_dir / "annotation").glob("*.gff"))
            + list((assembly_dir / "annotation").glob("*.gff3"))
        )
        gtf_paths = (
            list((assembly_dir / "annotation").glob("*.gtf.gz"))
            + list((assembly_dir / "annotation").glob("*.gtf"))
        )
        annotation_paths = gff_paths + gtf_paths
        metadata = read_source_metadata(assembly_dir)
        accession = accession_from_name(assembly_dir.name)
        species = species_from_name(assembly_dir.name)
        duplicate_group = accession or assembly_dir.name

        row = {
            "assembly_id": assembly_dir.name,
            "accession": accession,
            "species": metadata.get("organism_name", species).replace(" ", "_"),
            "genus": genus,
            "source_dir": str(assembly_dir),
            "genome_path": first_or_empty(genome_paths),
            "gff_path": first_or_empty(gff_paths),
            "gtf_path": first_or_empty(gtf_paths),
            "genome_gz_bytes": sum(p.stat().st_size for p in genome_paths if p.exists()),
            "annotation_gz_bytes": sum(p.stat().st_size for p in annotation_paths if p.exists()),
            "has_genome": int(bool(genome_paths)),
            "has_gff_or_gtf": int(bool(annotation_paths)),
            "train_eligible": int(bool(genome_paths and annotation_paths)),
            "duplicate_group_id": duplicate_group,
            "split_group": duplicate_group,
        }
        rows.append(row)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "assembly_id",
        "accession",
        "species",
        "genus",
        "source_dir",
        "genome_path",
        "gff_path",
        "gtf_path",
        "genome_gz_bytes",
        "annotation_gz_bytes",
        "has_genome",
        "has_gff_or_gtf",
        "train_eligible",
        "duplicate_group_id",
        "split_group",
    ]
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    eligible = sum(int(row["train_eligible"]) for row in rows)
    print(f"wrote {out}")
    print(f"brassicaceae_assemblies={len(rows)} train_eligible={eligible}")


if __name__ == "__main__":
    main()

