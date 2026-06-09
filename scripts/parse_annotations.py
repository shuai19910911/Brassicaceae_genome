#!/usr/bin/env python3
"""Parse GFF/GTF annotation features into TSV shards for structural supervision."""

from __future__ import annotations

import argparse
import csv
import gzip
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote


FEATURES = {"gene", "mrna", "transcript", "exon", "cds", "five_prime_utr", "three_prime_utr", "utr"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data_manifests/brassicaceae_assemblies.tsv")
    parser.add_argument("--out-dir", default="annotation_index")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--num-shards", type=int, default=1)
    return parser.parse_args()


def open_text(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path)


def read_manifest(path: Path, shard_index: int, num_shards: int) -> list[dict[str, str]]:
    with path.open() as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    rows = [row for row in rows if row.get("train_eligible") == "1" and (row.get("gff_path") or row.get("gtf_path"))]
    return [row for i, row in enumerate(rows) if i % num_shards == shard_index]


def parse_gff_attrs(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for part in raw.strip().split(";"):
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
        elif " " in part:
            key, value = part.split(" ", 1)
            value = value.strip().strip('"')
        else:
            continue
        attrs[key.strip()] = unquote(value.strip())
    return attrs


def infer_id(attrs: dict[str, str], feature: str, seqid: str, start0: int, end: int) -> str:
    for key in ("ID", "transcript_id", "gene_id", "Name", "locus_tag"):
        if key in attrs and attrs[key]:
            return attrs[key].split(",")[0]
    return f"{feature}:{seqid}:{start0}-{end}"


def parent_id(attrs: dict[str, str]) -> str:
    for key in ("Parent", "transcript_id", "gene_id"):
        if key in attrs and attrs[key]:
            return attrs[key].split(",")[0]
    return ""


def parse_file(row: dict[str, str]) -> tuple[list[dict[str, str | int]], list[dict[str, str | int]]]:
    path = row.get("gff_path") or row.get("gtf_path")
    features: list[dict[str, str | int]] = []
    transcripts: dict[str, dict[str, str | int]] = {}
    exons_by_parent: dict[str, list[tuple[int, int, str]]] = defaultdict(list)

    with open_text(path) as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 9:
                continue
            seqid, source, feature, start, end, score, strand, phase, attrs_raw = parts
            feature_l = feature.lower()
            if feature_l not in FEATURES:
                continue
            try:
                start0 = int(start) - 1
                end_i = int(end)
            except ValueError:
                continue
            attrs = parse_gff_attrs(attrs_raw)
            feature_id = infer_id(attrs, feature_l, seqid, start0, end_i)
            parent = parent_id(attrs)
            gene_id = attrs.get("gene_id") or attrs.get("gene") or parent
            transcript_id = attrs.get("transcript_id") or (feature_id if feature_l in {"mrna", "transcript"} else parent)
            biotype = (
                attrs.get("gene_biotype")
                or attrs.get("transcript_biotype")
                or attrs.get("biotype")
                or attrs.get("gbkey")
                or ""
            )
            record = {
                "assembly_id": row["assembly_id"],
                "seq_id": seqid,
                "standard_seq_id": f"{row['assembly_id']}|{seqid}",
                "source": source,
                "feature": feature_l,
                "start0": start0,
                "end": end_i,
                "strand": strand,
                "phase": phase,
                "feature_id": feature_id,
                "parent_id": parent,
                "gene_id": gene_id,
                "transcript_id": transcript_id,
                "biotype": biotype,
            }
            features.append(record)
            if feature_l in {"mrna", "transcript"}:
                transcripts[transcript_id] = record
            if feature_l == "exon" and transcript_id:
                exons_by_parent[transcript_id].append((start0, end_i, strand))

    introns: list[dict[str, str | int]] = []
    for tid, exons in exons_by_parent.items():
        if len(exons) < 2:
            continue
        exons_sorted = sorted(exons)
        for idx in range(len(exons_sorted) - 1):
            intron_start = exons_sorted[idx][1]
            intron_end = exons_sorted[idx + 1][0]
            if intron_end <= intron_start:
                continue
            strand = exons_sorted[idx][2]
            transcript_record = transcripts.get(tid, {})
            seqid = str(transcript_record.get("seq_id", ""))
            if not seqid:
                continue
            introns.append(
                {
                    "assembly_id": row["assembly_id"],
                    "seq_id": seqid,
                    "standard_seq_id": f"{row['assembly_id']}|{seqid}",
                    "source": "inferred",
                    "feature": "intron",
                    "start0": intron_start,
                    "end": intron_end,
                    "strand": strand,
                    "phase": ".",
                    "feature_id": f"{tid}:intron:{idx + 1}",
                    "parent_id": tid,
                    "gene_id": transcript_record.get("gene_id", ""),
                    "transcript_id": tid,
                    "biotype": transcript_record.get("biotype", ""),
                }
            )
    return features, introns


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_manifest(Path(args.manifest), args.shard_index, args.num_shards)
    out_path = out_dir / f"features.shard{args.shard_index:02d}.tsv"
    intron_path = out_dir / f"introns.shard{args.shard_index:02d}.tsv"
    fields = [
        "assembly_id",
        "seq_id",
        "standard_seq_id",
        "source",
        "feature",
        "start0",
        "end",
        "strand",
        "phase",
        "feature_id",
        "parent_id",
        "gene_id",
        "transcript_id",
        "biotype",
    ]
    with out_path.open("w", newline="") as feature_handle, intron_path.open("w", newline="") as intron_handle:
        feature_writer = csv.DictWriter(feature_handle, fieldnames=fields, delimiter="\t")
        intron_writer = csv.DictWriter(intron_handle, fieldnames=fields, delimiter="\t")
        feature_writer.writeheader()
        intron_writer.writeheader()
        for row in rows:
            features, introns = parse_file(row)
            feature_writer.writerows(features)
            intron_writer.writerows(introns)
            print(f"parsed {row['assembly_id']} features={len(features)} introns={len(introns)}")
    print(f"wrote {out_path}")
    print(f"wrote {intron_path}")


if __name__ == "__main__":
    main()

