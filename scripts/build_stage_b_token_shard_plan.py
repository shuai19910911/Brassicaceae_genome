#!/usr/bin/env python3
"""Build per-output-shard sampling targets for Stage B token materialization."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sampling-plan", default="data_manifests/stage_b_sampling_plan.tsv")
    parser.add_argument("--candidate-dir", default="sampling_index")
    parser.add_argument("--out", default="data_manifests/stage_b_token_shard_plan.tsv")
    parser.add_argument("--num-shards", type=int, default=12)
    parser.add_argument("--seed", default="BrassicaceaeGenomeFM_stage_b_v1")
    return parser.parse_args()


def context_label(context_len: int) -> str:
    return f"{context_len // 1024}k" if context_len % 1024 == 0 else str(context_len)


def stable_uint64(text: str) -> int:
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def load_targets(path: Path) -> dict[tuple[str, int, str], int]:
    targets = {}
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            targets[(row["split"], int(row["context_len"]), row["region"])] = int(row["target_windows"])
    return targets


def allocate_by_owner(owner_counts: dict[int, int], target_total: int, num_shards: int) -> dict[int, int]:
    available_total = sum(owner_counts.values())
    target_total = min(target_total, available_total)
    allocations = {}
    fractions = []
    for shard in range(num_shards):
        available = owner_counts.get(shard, 0)
        raw = target_total * available / available_total if available_total else 0
        target = min(available, int(raw))
        allocations[shard] = target
        fractions.append((raw - int(raw), shard))

    remaining = target_total - sum(allocations.values())
    for _, shard in sorted(fractions, reverse=True):
        if remaining == 0:
            break
        if allocations[shard] < owner_counts.get(shard, 0):
            allocations[shard] += 1
            remaining -= 1
    shard = 0
    while remaining > 0:
        if allocations[shard] < owner_counts.get(shard, 0):
            allocations[shard] += 1
            remaining -= 1
        shard = (shard + 1) % num_shards
    return allocations


def main() -> None:
    args = parse_args()
    targets = load_targets(Path(args.sampling_plan))
    contexts = sorted({key[1] for key in targets})
    counts: dict[tuple[str, int, str], dict[int, int]] = defaultdict(lambda: defaultdict(int))

    for context_len in contexts:
        for path in sorted(Path(args.candidate_dir).glob(f"region_candidates_{context_label(context_len)}.shard*.tsv")):
            with path.open() as handle:
                for row in csv.DictReader(handle, delimiter="\t"):
                    split = row["split"]
                    region = row["region"] if split == "train" else "all"
                    key = (split, int(row["context_len"]), region)
                    if key not in targets:
                        continue
                    row_id = "\t".join(
                        [
                            args.seed,
                            row["assembly_id"],
                            row["standard_seq_id"],
                            row["start0"],
                            row["end"],
                            row["context_len"],
                            split,
                            row["region"],
                        ]
                    )
                    owner = stable_uint64(row_id + "\towner") % args.num_shards
                    counts[key][owner] += 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "split",
                "context_len",
                "region",
                "shard_index",
                "available_windows",
                "target_windows",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        for key, target_total in targets.items():
            allocations = allocate_by_owner(counts[key], target_total, args.num_shards)
            for shard in range(args.num_shards):
                writer.writerow(
                    {
                        "split": key[0],
                        "context_len": key[1],
                        "region": key[2],
                        "shard_index": shard,
                        "available_windows": counts[key].get(shard, 0),
                        "target_windows": allocations[shard],
                    }
                )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
