#!/usr/bin/env python3
"""Build GPU-ready uint8 token shards for Stage B pretraining.

The script keeps the coordinate index as the reproducible source of truth, but
materializes the sampled windows into mmap-friendly binary shards so GPU
training does not repeatedly decompress FASTA files.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


TOKEN = bytes.maketrans(
    b"ACGTNacgtn",
    bytes([0, 1, 2, 3, 4, 0, 1, 2, 3, 4]),
)


@dataclass(frozen=True)
class Window:
    assembly_id: str
    seq_id: str
    standard_seq_id: str
    start0: int
    end: int
    context_len: int
    region: str
    split: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data_manifests/brassicaceae_assemblies.tsv")
    parser.add_argument("--raw-genome-root", default="")
    parser.add_argument("--sampling-plan", default="data_manifests/stage_b_sampling_plan.tsv")
    parser.add_argument("--shard-plan", default="data_manifests/stage_b_token_shard_plan.tsv")
    parser.add_argument("--candidate-dir", default="sampling_index")
    parser.add_argument("--out-dir", default="stage_b_token_shards")
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--num-shards", type=int, default=12)
    parser.add_argument("--seed", default="BrassicaceaeGenomeFM_stage_b_v1")
    return parser.parse_args()


def context_label(context_len: int) -> str:
    return f"{context_len // 1024}k" if context_len % 1024 == 0 else str(context_len)


def stable_uint64(text: str) -> int:
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def load_plan(path: Path, shard_index: int, num_shards: int, shard_plan: Path) -> dict[tuple[str, int, str], int]:
    targets: dict[tuple[str, int, str], int] = {}
    if shard_plan.exists():
        with shard_plan.open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if int(row["shard_index"]) != shard_index:
                    continue
                target = int(row["target_windows"])
                if target == 0:
                    continue
                targets[(row["split"], int(row["context_len"]), row["region"])] = target
        return targets

    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            total = int(row["target_windows"])
            base = total // num_shards
            extra = 1 if shard_index < total % num_shards else 0
            target = base + extra
            if target == 0:
                continue
            targets[(row["split"], int(row["context_len"]), row["region"])] = target
    return targets


def load_genome_paths(manifest: Path, raw_genome_root: str) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    with manifest.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            genome_path = Path(row["genome_path"])
            if raw_genome_root:
                genome_path = Path(raw_genome_root) / row["assembly_id"] / genome_path.name
            paths[row["assembly_id"]] = genome_path
    return paths


def maybe_keep(
    reservoirs: dict[tuple[str, int, str], list[tuple[int, str, Window]]],
    seen: dict[tuple[str, int, str], int],
    key: tuple[str, int, str],
    target: int,
    priority: int,
    row_id: str,
    window: Window,
) -> None:
    seen[key] += 1
    heap = reservoirs[key]
    item = (priority, row_id, window)
    if len(heap) < target:
        heapq.heappush(heap, item)
    elif priority > heap[0][0]:
        heapq.heapreplace(heap, item)


def select_windows(args: argparse.Namespace, targets: dict[tuple[str, int, str], int]) -> tuple[list[Window], dict[str, int]]:
    reservoirs: dict[tuple[str, int, str], list[tuple[int, str, Window]]] = defaultdict(list)
    seen: dict[tuple[str, int, str], int] = defaultdict(int)
    candidate_files = []
    for context_len in sorted({key[1] for key in targets}):
        candidate_files.extend(sorted(Path(args.candidate_dir).glob(f"region_candidates_{context_label(context_len)}.shard*.tsv")))

    for path in candidate_files:
        with path.open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                split = row["split"]
                context_len = int(row["context_len"])
                region = row["region"]
                key = (split, context_len, region if split == "train" else "all")
                target = targets.get(key)
                if target is None:
                    continue
                row_id = "\t".join(
                    [
                        args.seed,
                        row["assembly_id"],
                        row["standard_seq_id"],
                        row["start0"],
                        row["end"],
                        str(context_len),
                        split,
                        region,
                    ]
                )
                shard_owner = stable_uint64(row_id + "\towner") % args.num_shards
                if shard_owner != args.shard_index:
                    continue
                priority = stable_uint64(row_id + "\tpriority")
                maybe_keep(
                    reservoirs,
                    seen,
                    key,
                    target,
                    priority,
                    row_id,
                    Window(
                        assembly_id=row["assembly_id"],
                        seq_id=row["seq_id"],
                        standard_seq_id=row["standard_seq_id"],
                        start0=int(row["start0"]),
                        end=int(row["end"]),
                        context_len=context_len,
                        region=region,
                        split=split,
                    ),
                )

    selected = []
    shortfalls = {}
    for key, target in targets.items():
        heap = reservoirs.get(key, [])
        selected.extend(window for _, _, window in heap)
        if len(heap) < target:
            shortfalls["|".join(map(str, key))] = target - len(heap)
    selected.sort(key=lambda w: (w.assembly_id, w.standard_seq_id, w.start0, w.context_len, w.split, w.region))
    stats = {
        "selected_windows": len(selected),
        "candidate_groups": len(targets),
        "groups_with_shortfall": len(shortfalls),
    }
    if shortfalls:
        stats["shortfalls"] = shortfalls
    return selected, stats


def stream_fasta(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    seq_id = None
    chunks: list[str] = []
    with opener(path, "rt") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if seq_id is not None:
                    yield seq_id, "".join(chunks)
                seq_id = line[1:].split()[0]
                chunks = []
            else:
                chunks.append(line)
    if seq_id is not None:
        yield seq_id, "".join(chunks)


def encode_sequence(seq: str) -> bytes:
    raw = seq.encode("ascii", errors="ignore")
    encoded = raw.translate(TOKEN)
    return bytes(base if base <= 4 else 4 for base in encoded)


def write_shards(args: argparse.Namespace, windows: list[Window], genome_paths: dict[str, Path]) -> dict[str, int]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bin_handles = {}
    idx_handles = {}
    idx_writers = {}
    offsets = defaultdict(int)
    counts = defaultdict(int)
    token_counts = defaultdict(int)

    for split in ["train", "validation", "test"]:
        bin_path = out_dir / f"{split}_{args.shard_index:05d}.bin"
        idx_path = out_dir / f"{split}_{args.shard_index:05d}.idx.tsv"
        bin_handles[split] = bin_path.open("wb")
        idx_handles[split] = idx_path.open("w", newline="")
        writer = csv.DictWriter(
            idx_handles[split],
            fieldnames=[
                "split",
                "shard_index",
                "offset",
                "length",
                "assembly_id",
                "seq_id",
                "standard_seq_id",
                "start0",
                "end",
                "context_len",
                "region",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        idx_writers[split] = writer

    by_assembly: dict[str, list[Window]] = defaultdict(list)
    for window in windows:
        by_assembly[window.assembly_id].append(window)

    for assembly_id, assembly_windows in sorted(by_assembly.items()):
        by_seq: dict[str, list[Window]] = defaultdict(list)
        for window in assembly_windows:
            by_seq[window.seq_id].append(window)
        fasta_path = genome_paths[assembly_id]
        if not fasta_path.exists():
            raise FileNotFoundError(fasta_path)
        for seq_id, sequence in stream_fasta(fasta_path):
            seq_windows = by_seq.get(seq_id)
            if not seq_windows:
                continue
            for window in seq_windows:
                seq = sequence[window.start0 : window.end]
                if len(seq) != window.context_len:
                    raise ValueError(f"bad window length for {window}")
                encoded = encode_sequence(seq)
                split = window.split
                offset = offsets[split]
                bin_handles[split].write(encoded)
                idx_writers[split].writerow(
                    {
                        "split": split,
                        "shard_index": args.shard_index,
                        "offset": offset,
                        "length": len(encoded),
                        "assembly_id": window.assembly_id,
                        "seq_id": window.seq_id,
                        "standard_seq_id": window.standard_seq_id,
                        "start0": window.start0,
                        "end": window.end,
                        "context_len": window.context_len,
                        "region": window.region,
                    }
                )
                offsets[split] += len(encoded)
                counts[split] += 1
                token_counts[split] += len(encoded)

    for handle in bin_handles.values():
        handle.close()
    for handle in idx_handles.values():
        handle.close()

    return {
        "train_windows": counts["train"],
        "validation_windows": counts["validation"],
        "test_windows": counts["test"],
        "train_tokens": token_counts["train"],
        "validation_tokens": token_counts["validation"],
        "test_tokens": token_counts["test"],
    }


def main() -> None:
    args = parse_args()
    targets = load_plan(Path(args.sampling_plan), args.shard_index, args.num_shards, Path(args.shard_plan))
    windows, selection_stats = select_windows(args, targets)
    genome_paths = load_genome_paths(Path(args.manifest), args.raw_genome_root)
    write_stats = write_shards(args, windows, genome_paths)
    out_dir = Path(args.out_dir)
    stats = {
        "shard_index": args.shard_index,
        "num_shards": args.num_shards,
        "seed": args.seed,
        **selection_stats,
        **write_stats,
    }
    stats_path = out_dir / f"shard_{args.shard_index:05d}.stats.json"
    stats_path.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n")
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
