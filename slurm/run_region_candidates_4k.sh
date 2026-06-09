#!/usr/bin/env bash
#SBATCH -J brass_reg4k
#SBATCH -p q08
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -o logs/slurm/region_candidates_4k_%A_%a.out
#SBATCH -e logs/slurm/region_candidates_4k_%A_%a.err
#SBATCH --array=0-2

set -euo pipefail
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel
mkdir -p logs/slurm sampling_index

mamba run -n shizihuake python scripts/build_region_candidates.py \
  --contigs sequence_index/contigs.tsv \
  --splits data_manifests/brassicaceae_splits.tsv \
  --annotation-dir annotation_index \
  --out-dir sampling_index \
  --shard-index "${SLURM_ARRAY_TASK_ID}" \
  --num-shards 3 \
  --context-len 4096 \
  --background-stride 32768

