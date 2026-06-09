#!/usr/bin/env bash
#SBATCH -J brass_tokB
#SBATCH -p q08
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -o logs/slurm/token_shards_%x_%A_%a.out
#SBATCH -e logs/slurm/token_shards_%x_%A_%a.err
#SBATCH --array=0-11

set -euo pipefail
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel

: "${STAGE_NAME:=stage_b}"
: "${SAMPLING_PLAN:=data_manifests/${STAGE_NAME}_sampling_plan.tsv}"
: "${SHARD_PLAN:=data_manifests/${STAGE_NAME}_token_shard_plan.tsv}"
: "${OUT_DIR:=${STAGE_NAME}_token_shards}"
: "${NUM_SHARDS:=12}"
: "${SEED:=BrassicaceaeGenomeFM_${STAGE_NAME}_v1}"

mkdir -p logs/slurm "${OUT_DIR}"

python3 scripts/build_stage_b_token_shards.py \
  --shard-index "${SLURM_ARRAY_TASK_ID}" \
  --num-shards "${NUM_SHARDS}" \
  --sampling-plan "${SAMPLING_PLAN}" \
  --shard-plan "${SHARD_PLAN}" \
  --out-dir "${OUT_DIR}" \
  --seed "${SEED}"
