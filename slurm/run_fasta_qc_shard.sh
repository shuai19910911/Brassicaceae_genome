#!/usr/bin/env bash
#SBATCH -J brass_fasta_qc
#SBATCH -p q07
#SBATCH -c 30
#SBATCH --mem=150G
#SBATCH -o logs/slurm/fasta_qc_%A_%a.out
#SBATCH -e logs/slurm/fasta_qc_%A_%a.err
#SBATCH --array=0-2

set -euo pipefail
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel
mkdir -p logs/slurm sequence_index

mamba run -n shizihuake python scripts/fasta_qc.py \
  --manifest data_manifests/brassicaceae_assemblies.tsv \
  --out-dir sequence_index \
  --shard-index "${SLURM_ARRAY_TASK_ID}" \
  --num-shards 3

