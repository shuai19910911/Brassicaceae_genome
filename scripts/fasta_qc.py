#!/usr/bin/env python3
"""Stream FASTA files and produce contig-level QC tables."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data_manifests/brassicaceae_assemblies.tsv")
    parser.add_argument("--out-dir", default="sequence_index")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--min-contig-len", type=int, default=10_000)
    return parser.parse_args()


def open_text(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path)


def read_manifest(path: Path, shard_index: int, num_shards: int) -> list[dict[str, str]]:
    with path.open() as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    rows = [row for row in rows if row.get("train_eligible") == "1" and row.get("genome_path")]
    return [row for i, row in enumerate(rows) if i % num_shards == shard_index]


def classify_seq(seq_id: str) -> str:
    low = seq_id.lower()
    if any(word in low for word in ("mitochond", "mito", "chloroplast", "plastid", "pltd", "ptg")):
        return "organelle_or_plastid"
    return "nuclear_or_unknown"


def finalize_record(assembly_id: str, seq_id: str, chunks: list[str], min_len: int) -> dict[str, str | int | float]:
    seq = "".join(chunks).upper()
    length = len(seq)
    counts = {base: seq.count(base) for base in "ACGTN"}
    non_acgtn = length - sum(counts.values())
    n_count = counts["N"] + non_acgtn
    gc_count = counts["G"] + counts["C"]
    max_n_run = 0
    cur = 0
    for base in seq:
        if base == "N" or base not in "ACGT":
            cur += 1
            if cur > max_n_run:
                max_n_run = cur
        else:
            cur = 0
    n_fraction = n_count / length if length else 1.0
    gc_fraction = gc_count / max(1, counts["A"] + counts["C"] + counts["G"] + counts["T"])
    pass_qc = int(
        length >= min_len
        and n_fraction <= 0.10
        and max_n_run < 5_000
        and classify_seq(seq_id) == "nuclear_or_unknown"
    )
    return {
        "assembly_id": assembly_id,
        "seq_id": seq_id,
        "standard_seq_id": f"{assembly_id}|{seq_id}",
        "length": length,
        "a_count": counts["A"],
        "c_count": counts["C"],
        "g_count": counts["G"],
        "t_count": counts["T"],
        "n_count": n_count,
        "non_acgtn_count": non_acgtn,
        "gc_fraction": f"{gc_fraction:.6f}",
        "n_fraction": f"{n_fraction:.6f}",
        "max_n_run": max_n_run,
        "seq_class": classify_seq(seq_id),
        "pass_qc": pass_qc,
    }


def scan_fasta(row: dict[str, str], min_len: int) -> tuple[list[dict[str, str | int | float]], str]:
    genome_path = row["genome_path"]
    checksum = hashlib.sha256()
    records: list[dict[str, str | int | float]] = []
    seq_id = ""
    chunks: list[str] = []
    with open(genome_path, "rb") as raw:
        for block in iter(lambda: raw.read(1024 * 1024), b""):
            checksum.update(block)
    with open_text(genome_path) as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith(">"):
                if seq_id:
                    records.append(finalize_record(row["assembly_id"], seq_id, chunks, min_len))
                seq_id = line[1:].split()[0]
                chunks = []
            else:
                chunks.append(line.strip())
        if seq_id:
            records.append(finalize_record(row["assembly_id"], seq_id, chunks, min_len))
    return records, checksum.hexdigest()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_manifest(Path(args.manifest), args.shard_index, args.num_shards)

    contig_path = out_dir / f"contigs.shard{args.shard_index:02d}.tsv"
    assembly_path = out_dir / f"assembly_qc.shard{args.shard_index:02d}.tsv"
    checksum_path = out_dir / f"fasta_checksums.shard{args.shard_index:02d}.tsv"
    contig_fields = [
        "assembly_id",
        "seq_id",
        "standard_seq_id",
        "length",
        "a_count",
        "c_count",
        "g_count",
        "t_count",
        "n_count",
        "non_acgtn_count",
        "gc_fraction",
        "n_fraction",
        "max_n_run",
        "seq_class",
        "pass_qc",
    ]
    with contig_path.open("w", newline="") as contig_handle, assembly_path.open("w", newline="") as assembly_handle, checksum_path.open("w", newline="") as checksum_handle:
        contig_writer = csv.DictWriter(contig_handle, fieldnames=contig_fields, delimiter="\t")
        contig_writer.writeheader()
        assembly_writer = csv.DictWriter(
            assembly_handle,
            fieldnames=["assembly_id", "contigs", "pass_contigs", "total_bp", "pass_bp", "qc_status"],
            delimiter="\t",
        )
        assembly_writer.writeheader()
        checksum_writer = csv.DictWriter(
            checksum_handle,
            fieldnames=["assembly_id", "genome_path", "sha256"],
            delimiter="\t",
        )
        checksum_writer.writeheader()
        for row in rows:
            records, digest = scan_fasta(row, args.min_contig_len)
            for record in records:
                contig_writer.writerow(record)
            total_bp = sum(int(record["length"]) for record in records)
            pass_bp = sum(int(record["length"]) for record in records if int(record["pass_qc"]) == 1)
            pass_contigs = sum(1 for record in records if int(record["pass_qc"]) == 1)
            assembly_writer.writerow(
                {
                    "assembly_id": row["assembly_id"],
                    "contigs": len(records),
                    "pass_contigs": pass_contigs,
                    "total_bp": total_bp,
                    "pass_bp": pass_bp,
                    "qc_status": "pass" if pass_bp > 0 else "fail",
                }
            )
            checksum_writer.writerow(
                {"assembly_id": row["assembly_id"], "genome_path": row["genome_path"], "sha256": digest}
            )
            print(f"scanned {row['assembly_id']} contigs={len(records)} pass_contigs={pass_contigs}")

    print(f"wrote {contig_path}")
    print(f"wrote {assembly_path}")
    print(f"wrote {checksum_path}")


if __name__ == "__main__":
    main()

