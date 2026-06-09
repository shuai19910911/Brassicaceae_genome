#!/usr/bin/env python3
"""Create a formal mixed-context Stage B sampling plan from candidate summaries."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


TARGET_REGION_MIX = {
    "cds": 0.30,
    "exon": 0.15,
    "five_prime_utr": 0.05,
    "three_prime_utr": 0.05,
    "intron": 0.20,
    "gene": 0.05,
    "mrna": 0.03,
    "transcript": 0.02,
    "background": 0.15,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary-spec",
        action="append",
        default=[
            "4096:0.20:data_manifests/region_candidates_4k_summary.tsv",
            "8192:0.70:data_manifests/region_candidates_8k_summary.tsv",
            "16384:0.10:data_manifests/region_candidates_16k_summary.tsv",
        ],
        help="Context specification as context_len:token_fraction:summary_path. Repeatable.",
    )
    parser.add_argument("--out", default="data_manifests/stage_b_sampling_plan.tsv")
    parser.add_argument("--target-train-tokens", type=int, default=20_000_000_000)
    parser.add_argument("--validation-windows", type=int, default=50_000)
    parser.add_argument("--test-windows", type=int, default=50_000)
    return parser.parse_args()


def load_counts(path: Path) -> tuple[dict[str, int], dict[str, int]]:
    split_counts: dict[str, int] = {}
    region_counts: dict[str, int] = {}
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["metric"] == "split":
                split_counts[row["name"]] = int(row["count"])
            elif row["metric"] == "region":
                region_counts[row["name"]] = int(row["count"])
    return split_counts, region_counts


def main() -> None:
    args = parse_args()
    specs = []
    for spec in args.summary_spec:
        context_len_s, token_fraction_s, summary_path_s = spec.split(":", 2)
        specs.append((int(context_len_s), float(token_fraction_s), Path(summary_path_s)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "split",
                "context_len",
                "region",
                "available_windows",
                "target_windows",
                "target_tokens",
                "sampling_fraction_of_available",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        total_target_train_windows = 0
        for context_len, token_fraction, summary_path in specs:
            split_counts, region_counts = load_counts(summary_path)
            context_train_tokens = int(args.target_train_tokens * token_fraction)
            train_windows = context_train_tokens // context_len
            total_target_train_windows += train_windows
            for region, mix in TARGET_REGION_MIX.items():
                available = region_counts.get(region, 0)
                target = min(available, int(train_windows * mix))
                writer.writerow(
                    {
                        "split": "train",
                        "context_len": context_len,
                        "region": region,
                        "available_windows": available,
                        "target_windows": target,
                        "target_tokens": target * context_len,
                        "sampling_fraction_of_available": f"{target / available:.8f}" if available else "0.00000000",
                    }
                )
            for split, windows in (("validation", args.validation_windows), ("test", args.test_windows)):
                available = split_counts.get(split, 0)
                target = min(available, windows)
                writer.writerow(
                    {
                        "split": split,
                        "context_len": context_len,
                        "region": "all",
                        "available_windows": available,
                        "target_windows": target,
                        "target_tokens": target * context_len,
                        "sampling_fraction_of_available": f"{target / available:.8f}" if available else "0.00000000",
                    }
                )
    print(f"wrote {out}")
    print(f"target_train_windows={total_target_train_windows} target_train_tokens={args.target_train_tokens}")


if __name__ == "__main__":
    main()
