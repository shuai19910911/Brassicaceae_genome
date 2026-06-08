# BrassicaceaeGenomeFM 模型结构解析

更新时间：2026-06-08 23:16:12 CST

## 1. 模型定位

`BrassicaceaeGenomeFM-330M` 是十字花科结构注释驱动 DNA foundation model。第一版主模型采用单碱基 token、长上下文 bidirectional Mamba/Caduceus 风格 backbone、reverse-complement 一致性训练和多任务结构监督。

选择 Mamba/Caduceus 风格而不是纯 Transformer 的原因：

1. DNA 需要长上下文，纯 self-attention 在 64K-128K bp 训练成本过高。
2. 基因组序列天然存在 reverse-complement 对称性，Caduceus 已证明 RC 等变/一致性对 DNA 模型有价值。
3. 十字花科存在 polyploid Brassica、长 intron、TE 邻域和跨属保守元件，需要比 512 bp/6 kb 更长的上下文。
4. PlantCAD/PlantCaduceus 已证明 Caduceus/Mamba 架构适合植物跨物种任务。

## 2. 输入表示

### 2.1 Vocabulary

```text
0 PAD
1 A
2 C
3 G
4 T
5 N
6 MASK
7 BOS
8 EOS
```

第一版不使用 BPE/k-mer。原因：

- 单碱基 token 保留 splice site、codon frame、SNP/indel 变异效应的单碱基分辨率。
- BPE/k-mer 对长上下文更省 token，但会模糊边界监督，不适合作为第一版主模型。
- 后续可训练 BPE distillation 小模型用于快速 embedding。

### 2.2 输入字段

每个样本包含：

```text
input_ids: uint8, length L
attention_or_valid_mask: bool, length L
assembly_id
species_id
genus_id
contig_id
start
end
strand
context_bucket
region_bucket
region_weight_base
quality_flags
split
```

训练时动态生成：

```text
mask positions
MLM labels
RC direction
loss weights
batch order
```

## 3. Backbone

推荐主模型参数：

| 模块 | 设定 |
|---|---:|
| model name | BrassicaceaeGenomeFM-330M |
| total params | about 330M |
| layers | 32 |
| hidden size | 1024 |
| vocab embedding dim | 1024 |
| SSM state size | 64-128 |
| conv kernel | 4-8 |
| expansion factor | 2 |
| norm | RMSNorm |
| dropout | 0.05 |
| precision | bf16 |
| max trained context | 128K bp |

Block 结构：

```text
Input x
  -> RMSNorm
  -> forward Mamba branch
  -> reverse/complement-aware Mamba branch
  -> bidirectional merge / gated merge
  -> residual
  -> RMSNorm
  -> gated MLP
  -> residual
```

RC 一致性处理：

```text
seq = original sequence
rc_seq = reverse_complement(seq)
h_seq = model(seq)
h_rc = reverse_complement_align(model(rc_seq))
L_rc = mse(mean_pool(h_seq), mean_pool(h_rc)) + token-level consistency on sampled positions
```

## 4. Heads

### 4.1 Masked nucleotide LM head

输入：last hidden states。

输出：

```text
P(A/C/G/T/N) for masked positions
```

用途：主自监督预训练。

### 4.2 Region segmentation head

单碱基多类标签：

```text
intergenic
promoter
5UTR
CDS
intron
3UTR
splice_donor_flank
splice_acceptor_flank
start_codon_window
stop_codon_window
TE_or_repeat_proxy
unknown_or_unlabeled
```

输出：`L x num_region_classes`。

损失：weighted cross entropy / focal loss，忽略 unknown。

### 4.3 Boundary heads

二分类或局部多分类：

```text
splice donor
splice acceptor
start codon
stop codon
TSS proxy
TES proxy
```

处理类别不平衡：

```text
positive-centered sampling
hard negative near boundary
class-balanced focal loss
```

### 4.4 CDS frame head

输出：

```text
non-CDS
CDS frame 0
CDS frame 1
CDS frame 2
```

用途：让模型显式学习 reading frame 和编码区周期性。

### 4.5 Sequence embedding head

pooling：

```text
mean token pooling as default
masked mean pooling for valid positions
optional region-aware pooling
```

2025 DNA foundation model benchmark 显示 mean pooling 在多类序列分类任务中通常强于 summary token/max pooling，因此本项目默认下游 embedding 使用 mean pooling。

## 5. Loss 设计

总损失：

```text
L_total =
  1.00 * L_mlm
  + 0.30 * L_region
  + 0.25 * L_splice
  + 0.15 * L_start_stop
  + 0.10 * L_cds_frame
  + 0.10 * L_rc
```

Stage 动态权重：

| Stage | MLM | region | splice | start/stop | frame | RC |
|---|---:|---:|---:|---:|---:|---:|
| B | 1.00 | 0.20 | 0.15 | 0.10 | 0.05 | 0.05 |
| C1 | 1.00 | 0.30 | 0.25 | 0.15 | 0.10 | 0.10 |
| C2 | 1.00 | 0.30 | 0.25 | 0.15 | 0.10 | 0.10 |
| D | 1.00 | 0.20 | 0.15 | 0.10 | 0.05 | 0.15 |

## 6. Context curriculum

| Stage | Context | 目的 |
|---|---|---|
| B | 4K/8K/16K | 学习局部基因结构、splice、codon、短 promoter |
| C1 | 8K/16K/32K | 学习完整基因、长 intron、TSS/TES 邻域 |
| C2 | 32K/64K | 学习 gene-proximal TE、polyploid gene neighborhood |
| D | 64K/128K | 学习长程上下文和亚基因组背景 |

若显存不足，正式第一版最低完成到 C2，即 64K context；D 作为增强阶段。

## 7. Optimizer 与训练超参

推荐：

```text
optimizer: AdamW
lr peak: 2e-4 for 330M
min lr: 2e-5
weight decay: 0.1
beta1: 0.9
beta2: 0.95
warmup: 2%-5% total steps
scheduler: cosine decay
precision: bf16
gradient clipping: 1.0
gradient checkpointing: yes
activation checkpointing: yes
dynamic masking rate: 15%
mask replacement: 80% MASK, 10% random nucleotide, 10% unchanged
RC augmentation probability: 0.5
```

Batch 原则：

```text
按 token batch，不按样本数 batch
优先保持每 GPU token 数稳定
长 context 使用 gradient accumulation
不同 context bucket 分桶 batch，避免 padding 浪费
```

## 8. GPU 命令模板

用户在 GPU 节点执行，示例：

```bash
CUDA_VISIBLE_DEVICES=1,2 python train.py --config configs/train_stage_b.yaml
CUDA_VISIBLE_DEVICES=1,2 python train.py --config configs/train_stage_c1.yaml --resume checkpoints/stage_b_last
CUDA_VISIBLE_DEVICES=1,2 python train.py --config configs/train_stage_c2.yaml --resume checkpoints/stage_c1_last
CUDA_VISIBLE_DEVICES=1,2 python train.py --config configs/train_stage_d.yaml --resume checkpoints/stage_c2_last
```

## 9. 产物

训练完成后应至少产出：

```text
checkpoints/brassicaceae_genomefm_330m_stage_b
checkpoints/brassicaceae_genomefm_330m_stage_c1
checkpoints/brassicaceae_genomefm_330m_stage_c2
checkpoints/brassicaceae_genomefm_330m_stage_d_optional
results/downstream_benchmark_summary.tsv
results/model_card.md
```

GitHub 只放摘要和模型卡，不放 checkpoint。

