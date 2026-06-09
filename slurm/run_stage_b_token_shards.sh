#!/usr/bin/env bash
#SBATCH -J brass_tokB
#SBATCH -p q08
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -o logs/slurm/stage_b_token_shards_%A_%a.out
#SBATCH -e logs/slurm/stage_b_token_shards_%A_%a.err
#SBATCH --array=0-11

set -euo pipefail
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel
mkdir -p logs/slurm stage_b_token_shards

python3 scripts/build_stage_b_token_shards.py \
  --shard-index "${SLURM_ARRAY_TASK_ID}" \
  --num-shards 12 \
  --out-dir stage_b_token_shards
