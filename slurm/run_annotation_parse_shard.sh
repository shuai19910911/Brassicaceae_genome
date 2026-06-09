#!/usr/bin/env bash
#SBATCH -J brass_gff_parse
#SBATCH -p q08
#SBATCH -c 30
#SBATCH --mem=150G
#SBATCH -o logs/slurm/annotation_parse_%A_%a.out
#SBATCH -e logs/slurm/annotation_parse_%A_%a.err
#SBATCH --array=0-2

set -euo pipefail
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel
mkdir -p logs/slurm annotation_index

mamba run -n shizihuake python scripts/parse_annotations.py \
  --manifest data_manifests/brassicaceae_assemblies.tsv \
  --out-dir annotation_index \
  --shard-index "${SLURM_ARRAY_TASK_ID}" \
  --num-shards 3

