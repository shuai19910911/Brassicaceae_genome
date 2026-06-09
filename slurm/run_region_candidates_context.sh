#!/usr/bin/env bash
#SBATCH -J brass_regctx
#SBATCH -p q08
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -o logs/slurm/region_candidates_ctx_%A_%a.out
#SBATCH -e logs/slurm/region_candidates_ctx_%A_%a.err
#SBATCH --array=0-2

set -euo pipefail
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel
mkdir -p logs/slurm sampling_index

: "${CONTEXT_LEN:?set CONTEXT_LEN, e.g. 32768}"
: "${BACKGROUND_STRIDE:?set BACKGROUND_STRIDE, e.g. 262144}"

python3 scripts/build_region_candidates.py \
  --contigs sequence_index/contigs.tsv \
  --splits data_manifests/brassicaceae_splits.tsv \
  --annotation-dir annotation_index \
  --out-dir sampling_index \
  --shard-index "${SLURM_ARRAY_TASK_ID}" \
  --num-shards 3 \
  --context-len "${CONTEXT_LEN}" \
  --background-stride "${BACKGROUND_STRIDE}"
