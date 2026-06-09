#!/usr/bin/env bash
#SBATCH -J brass_ann_qc
#SBATCH -p q07
#SBATCH -c 30
#SBATCH --mem=150G
#SBATCH -o logs/slurm/annotation_qc_summary_%j.out
#SBATCH -e logs/slurm/annotation_qc_summary_%j.err

set -euo pipefail
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel
mkdir -p logs/slurm annotation_index

mamba run -n shizihuake python scripts/summarize_annotation_qc.py \
  --contigs sequence_index/contigs.tsv \
  --annotation-dir annotation_index \
  --out-dir annotation_index

