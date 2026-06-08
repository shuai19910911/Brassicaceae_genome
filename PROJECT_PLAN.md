# BrassicaceaeGenomeFM 十字花科基因组预训练大模型完整训练计划

更新时间：2026-06-08 23:16:12 CST

## 1. 项目目标

训练一个面向十字花科的正式 DNA foundation model：`BrassicaceaeGenomeFM-330M`。模型必须学习十字花科基因组中的基因结构、剪接边界、CDS reading frame、UTR、启动子/TSS 邻域、TES、内含子、TE/repeat 背景、polyploid Brassica 亚基因组差异和跨属保守序列模式。

第一版目标不是 genome-only 语言模型，而是结构注释驱动模型。正式训练数据必须同时满足：

```text
has_genome = yes
has_structural_annotation = yes
genome_qc_status = pass after local scan
annotation_qc_status = pass or usable after local parse
```

## 2. 前沿依据与技术选择

当前 DNA/plant genome foundation model 的有效方向如下：

- Nucleotide Transformer 证明大规模多物种 DNA 预训练可以迁移到 splice、enhancer、promoter 等多类任务，并发布 50M 到 2.5B 参数规模模型。
- DNABERT-2 用 BPE 取代固定 k-mer，在多物种基因组上提高效率，但短/中上下文仍不足以覆盖 Brassica 长 intron、TE 邻域和远端调控区。
- HyenaDNA 证明单碱基分辨率可扩展到超长 DNA 上下文，适合长距离依赖建模。
- Caduceus 将 Mamba 改造为双向、reverse-complement 等变的 DNA 序列模型，适合 DNA 正反链对称性。
- PlantCAD/PlantCaduceus 使用 Caduceus/Mamba 结构在植物跨物种任务上表现强，PlantCAD2 已扩展到 8,192 bp 输入和 88M/311M/694M 三档模型。
- 2025 DNA foundation model benchmark 显示，通用 DNA 模型在部分任务有效，但表达、QTL、变异效应和多物种功能任务需要领域数据、合适 pooling 和任务专用头。
- GPN 在 Arabidopsis 中证明自监督 DNA 模型可以学习跨物种保守性与变异效应信号。
- SegmentNT 说明在预训练 DNA foundation model 上接 U-Net/segmentation head，可做单碱基分辨率的基因组元素标注。

因此本项目采用：

```text
single-nucleotide tokenization
bidirectional Mamba / Caduceus-style backbone
reverse-complement consistency
long-context curriculum: 8K -> 32K -> 64K -> 128K
masked nucleotide modeling + annotation-aware auxiliary losses
region-aware and genus-aware weighted sampling
formal downstream benchmark, not toy testing
```

参考来源：

- Nucleotide Transformer: https://pubmed.ncbi.nlm.nih.gov/39609566/
- DNABERT-2: https://arxiv.org/abs/2306.15006
- HyenaDNA: https://arxiv.org/abs/2306.15794
- Caduceus: https://arxiv.org/abs/2403.03234
- PlantCAD/PlantCaduceus: https://github.com/plantcad/plantcad
- PlantCaduceus paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC12184517/
- DNA FM benchmark: https://www.nature.com/articles/s41467-025-65823-8
- GPN Arabidopsis: https://pmc.ncbi.nlm.nih.gov/articles/PMC10622914/
- SegmentNT: https://pmc.ncbi.nlm.nih.gov/articles/PMC12615259/
- Plant foundation model review: https://pmc.ncbi.nlm.nih.gov/articles/PMC12170578/
- AgroNT: https://pubmed.ncbi.nlm.nih.gov/38982288/

## 3. 当前数据盘点

原始目录：

```text
/home/user/zhangzhishuai/data/plantDB/genome
```

本地统计时间：2026-06-08 23:16:12 CST。

| 数据项 | 数量/体积 |
|---|---:|
| 十字花科候选 assembly | 220 |
| genome FASTA 可用 assembly | 220 |
| genome + GFF/GTF 结构注释可用 assembly | 67 |
| 注释可用 genome `.fna.gz` 合计 | 8.22 GB |
| 注释 `.gff/.gff3/.gtf.gz` 合计 | 0.86 GB |

67 个注释可用 assembly 的属分布：

| 属 | assembly 数 |
|---|---:|
| Arabidopsis | 15 |
| Arabis | 4 |
| Brassica | 29 |
| Camelina | 1 |
| Capsella | 2 |
| Cardamine | 5 |
| Noccaea | 2 |
| Sinapis | 1 |
| Thlaspi | 8 |

正式训练第一版只使用这 67 个注释可用 assembly。无注释 genome 暂不混入，原因是：

1. 主目标是结构注释驱动，不是单纯拟合碱基分布。
2. 无 GFF/GTF 无法可靠提供 exon、CDS、intron、UTR、splice、TSS/TES 标签。
3. 大量无注释 Brassica napus genome 会强烈主导采样，稀释 Arabidopsis/Thlaspi/Cardamine 等跨属监督信号。
4. 后续可在模型收敛后用无注释 genome 做低权重 continual pretraining 或 embedding 泛化评估。

## 4. 本地目录设计

所有项目文件放在当前仓库，原始 genome 目录只读。

| 目录 | 内容 | 是否上传 GitHub | 预计体积 |
|---|---|---:|---:|
| `data_manifests/` | assembly 清单、split、统计摘要 | 是，仅小 TSV/MD | < 100 MB |
| `sequence_index/` | contig 长度、GC、N、softmask、checksum | 否 | 1-5 GB |
| `annotation_index/` | gene/transcript/exon/CDS/UTR/intron/TSS/TES parquet | 否 | 2-20 GB |
| `sampling_index/` | 候选窗口、区域权重、split map | 否 | 2-20 GB |
| `stage_inputs/` | Stage B/C1/C2/D 固化输入 | 否 | 30-120 GB |
| `training_server_transfer/` | 给 GPU 服务器搬运的当前 stage 数据与配置 | 否，只放说明 | 20-80 GB/stage |
| `configs/` | 数据、模型、训练 YAML | 是 | < 100 MB |
| `logs/` | CPU/GPU 日志 | 否 | 10-50 GB |
| `checkpoints/` | GPU 训练 checkpoint | 否 | 100-500 GB |
| `results/` | 下游任务输出 | 否，摘要可上传 | 20-200 GB |

## 5. 数据预处理

### 5.1 Assembly manifest

输入：

```text
/home/user/zhangzhishuai/data/plantDB/genome/*/genome/*.fna.gz
/home/user/zhangzhishuai/data/plantDB/genome/*/annotation/*.gff*.gz
/home/user/zhangzhishuai/data/plantDB/genome/*/annotation/*.gtf.gz
```

输出：

```text
data_manifests/brassicaceae_assemblies.tsv
```

字段：

```text
assembly_id
accession
species
genus
source_dir
genome_path
gff_path
gtf_path
genome_gz_bytes
annotation_gz_bytes
has_genome
has_gff_or_gtf
train_eligible
duplicate_group_id
split_group
```

资源与时间：

```text
CPU: 4-8 cores
RAM: 8-16 GB
运行位置: 登录节点可运行，正式建议 q07/q08
预计时间: 5-20 min
```

SLURM 示例：

```bash
mamba run -n shizihuake python scripts/build_manifest.py
```

### 5.2 FASTA 标准化与质量扫描

处理规则：

1. 流式读取 `.fna.gz`，不整体解压。
2. header 标准化为 `assembly_id|seq_id`。
3. 碱基统一大写，非 A/C/G/T/N 转为 N。
4. contig length `< 10 kb` 不进入主训练。
5. contig N fraction `> 10%` 不进入主训练。
6. contig N fraction `5%-10%` 只允许低权重非关键背景区域。
7. 连续 N `>= 1 kb` 标记为切分断点，连续 N `>= 5 kb` 强制断开窗口。
8. organelle/plastid/mitochondrial 序列单独标记，第一版不混入核基因组主训练。
9. 生成 `.fai`、contig table、checksum table。

输出：

```text
sequence_index/contigs.tsv
sequence_index/assembly_qc.tsv
sequence_index/fasta_checksums.tsv
```

资源与时间：

```text
CPU: 2-4 个 SLURM 作业，每个 30 cores
RAM: 80-150 GB/job
预计时间: 6-18 h
```

SLURM 示例：

```bash
sbatch -p q07 -c 30 run_fasta_qc.sh
```

### 5.3 GFF/GTF 结构注释解析

内部统一坐标：

```text
0-based half-open
strand-aware
seqid mapped to standardized FASTA header
```

解析内容：

```text
gene
transcript/mRNA
exon
CDS
UTR
intron inferred from exon chain
splice donor/acceptor inferred from exon-intron junctions
start/stop codon inferred from CDS
TSS/TES inferred by strand
```

质量控制：

1. 坐标必须在 contig 长度范围内。
2. transcript/exon/CDS parent-child 关系必须可追踪。
3. exon 顺序必须合法。
4. CDS phase 明显冲突、CDS 长度非 3 倍数的 transcript 不用于 CDS/frame 监督。
5. 多转录本基因选择 canonical transcript 作为主结构，其他 isoform 保留为低权重边界监督。
6. protein-coding、lncRNA、pseudogene、TE gene 分开标记。

输出：

```text
annotation_index/genes.parquet
annotation_index/transcripts.parquet
annotation_index/exons.parquet
annotation_index/cds.parquet
annotation_index/utrs.parquet
annotation_index/introns.parquet
annotation_index/splice_sites.parquet
annotation_index/tss_tes.parquet
```

资源与时间：

```text
CPU: 2-4 个 SLURM 作业，每个 30 cores
RAM: 80-150 GB/job
预计时间: 8-24 h
```

### 5.4 功能区域构建

区域标签：

| 区域 | 定义 |
|---|---|
| CDS | protein-coding CDS |
| coding exon | protein-coding exon |
| 5UTR/3UTR | GFF/GTF 可解析 UTR |
| intron | transcript 内 exon 间区间 |
| splice donor | exon-intron junction donor flank |
| splice acceptor | intron-exon junction acceptor flank |
| start codon window | start codon 上下游 2 kb |
| stop codon window | stop codon 上下游 2 kb |
| promoter/TSS | TSS upstream 5 kb + downstream 1 kb |
| TES/polyA proxy | TES 上下游 3 kb |
| gene-proximal intergenic | gene 20 kb 内 intergenic |
| distal intergenic | 远离 gene 的高质量背景 |
| TE/repeat proxy | softmask 或可用 repeat annotation 区域；无 repeat 注释时不伪标 |

输出：

```text
annotation_index/regions.parquet
sampling_index/region_candidates.parquet
sampling_index/region_weights.tsv
```

资源与时间：

```text
CPU: 1-3 个 SLURM 作业，每个 30 cores
RAM: 80-150 GB/job
预计时间: 6-18 h
```

### 5.5 Split 与防泄漏

正式 split 规则：

1. 先 split，后采样。
2. 同一 assembly 不跨 train/val/test。
3. 同一 duplicate_group 不跨 split。
4. Arabidopsis thaliana TAIR10 保留为核心开发/benchmark 参考，但不能让同源 accession 泄漏到 test。
5. Brassica napus 大量 accession 需要按 accession/来源分组，避免近重复 genome 泄漏。
6. 小属至少保留 validation/test 代表，但不得牺牲训练中跨属覆盖。

推荐比例：

```text
train: 80%
validation: 10%
test: 10%
```

特殊保留：

```text
Arabidopsis/Capsella/Cardamine/Thlaspi 各保留跨属 test
Brassica napus/rapa/oleracea 保留 polyploid/subgenome test
```

### 5.6 候选窗口与区域保留比例

硬过滤：

```text
train 默认 N <= 5%
5% < N <= 10% 只允许稀缺区域低权重救援
validation/test N <= 5%
关键监督窗口 N <= 2%
任意连续 N >= 1 kb 的窗口默认丢弃
单一碱基比例 > 80% 的窗口丢弃
contig 边缘不足 1 kb 的纯背景窗口丢弃
```

区域保留：

| 区域 | 保留策略 |
|---|---|
| CDS/coding exon | 100% |
| splice donor/acceptor flank | 100%，上下游至少 2 kb |
| start/stop codon neighborhood | 100%，上下游至少 2 kb |
| UTR | 100% |
| promoter/TSS 0-5 kb | 100% |
| promoter/TSS 5-20 kb | 15% 高质量代表 |
| intron boundary +/-2 kb | 100% |
| ordinary intron | 10% |
| long intron >20 kb | 5%，优先低 N 高复杂度 |
| TE/repeat near gene/promoter 20 kb | 100% |
| other TE/repeat | 50% |
| gene-proximal intergenic | 10% |
| distal intergenic | 3%-5% |
| random genome background | 1%-2% |

采样平衡：

```text
Brassica 总 token 占比上限: 55%-60%
Arabidopsis 总 token 占比下限: 8%-12%
小属合计 token 占比下限: 15%-20%
单一 assembly token 占比上限: 5%
distal intergenic token 占比上限: 10%
```

## 6. 输入模型方式

### 6.1 Tokenization

第一版采用单碱基 token：

```text
A C G T N MASK PAD BOS EOS
```

内部 `input_ids` 使用 `uint8`。训练时动态处理：

```text
dynamic masked nucleotide modeling labels
dynamic reverse-complement augmentation
dynamic strand sampling
dynamic batch ordering
dynamic region-loss weights
```

不提前固化：

```text
mask positions
MLM labels
RC direction
batch order
dropout/random seed sequence
```

### 6.2 Stage input 固化

本服务器按 stage 固化窗口或 `input_ids`，GPU 训练服务器只搬运当前 stage。

| Stage | 上下文组成 | token 预算 | 固化输入估算体积 | 目的 |
|---|---|---:|---:|---|
| Stage B | 70% 8K + 20% 4K + 10% 16K | 20B-50B | 25-70 GB | 主体短中上下文学习 |
| Stage C1 | 70% 32K + 20% 8K + 10% 16K | 10B-25B | 12-40 GB | intron/promoter/TE 邻域 |
| Stage C2 | 70% 64K + 20% 32K + 10% 8K | 5B-15B | 6-25 GB | 长基因与亚基因组上下文 |
| Stage D | 70% 128K + 20% 64K + 10% 32K | 2B-8B | 3-15 GB | 长上下文适配 |

由于本项目第一版注释可用数据规模小于作物/豆科项目，token 预算按多 epoch、动态 mask、区域重采样实现。若后续补齐无注释 genome 的结构注释，Stage B/C token 预算可上调。

## 7. 模型架构

正式模型：`BrassicaceaeGenomeFM-330M`

总体结构：

```text
single-nucleotide embedding
RC-aware embedding / RC consistency path
bidirectional Mamba blocks
RMSNorm
gated MLP
masked nucleotide LM head
region segmentation head
splice/start/stop boundary heads
sequence-level embedding head
```

核心参数：

| 参数 | 设定 |
|---|---:|
| 参数量 | 约 330M |
| layers | 32 |
| hidden size | 1024 |
| SSM state size | 64-128 |
| conv kernel | 4-8 |
| expansion factor | 2 |
| vocab size | 9 |
| max context stage | 128K bp |
| dropout | 0.05 |
| norm | RMSNorm |
| precision | bf16 |
| gradient checkpointing | yes |

损失函数：

```text
L = 1.00 * MLM
  + 0.30 * region segmentation
  + 0.25 * splice donor/acceptor
  + 0.15 * start/stop codon
  + 0.10 * CDS frame
  + 0.10 * RC consistency
```

更多结构细节见 [MODEL_STRUCTURE.md](MODEL_STRUCTURE.md)。

## 8. 训练计划与资源估计

### 8.1 CPU 预处理

登录节点只做轻量检查。正式 CPU 任务提交到 q07/q08：

```bash
sbatch -p q07 -c 30 run.sh
```

每次最多提交 6 个命令。使用环境：

```bash
mamba run -n shizihuake <command>
```

CPU 阶段估计：

| 阶段 | 作业数 | 每作业资源 | 预计时间 |
|---|---:|---|---:|
| manifest | 1 | 4-8 CPU, 16 GB | 5-20 min |
| FASTA QC | 2-4 | 30 CPU, 80-150 GB | 6-18 h |
| GFF/GTF parse | 2-4 | 30 CPU, 80-150 GB | 8-24 h |
| region build | 1-3 | 30 CPU, 80-150 GB | 6-18 h |
| split + leakage check | 1 | 16-30 CPU, 64 GB | 1-4 h |
| sampling index | 2-4 | 30 CPU, 100-150 GB | 8-24 h |
| stage input build | 2-6 | 30 CPU, 100-150 GB | 12-48 h |

CPU 总时间：

```text
顺序执行: 3-7 天
合理并行: 2-4 天
```

### 8.2 GPU 训练

GPU 训练由用户执行。命令风格：

```bash
CUDA_VISIBLE_DEVICES=1,2 python train.py --config configs/train_stage_b.yaml
```

推荐资源：

| 配置 | 作用 | 预计时间 |
|---|---|---:|
| 2x A100 80G 或同级 | 可训练 330M，8K/32K 稳定，64K 需 checkpointing | 10-25 天 |
| 4x A100 80G 或同级 | 推荐正式训练 | 6-14 天 |
| 8x A100/H100 | 更稳，支持更大 batch 和 128K | 4-9 天 |

训练 stage 估计：

| Stage | context | token 预算 | 2 GPU 估计 | 4 GPU 估计 |
|---|---|---:|---:|---:|
| B | 4K/8K/16K | 20B-50B | 5-12 天 | 3-7 天 |
| C1 | 8K/16K/32K | 10B-25B | 3-7 天 | 2-4 天 |
| C2 | 32K/64K | 5B-15B | 2-5 天 | 1-3 天 |
| D | 64K/128K | 2B-8B | 1-4 天 | 1-2 天 |
| downstream precompute | embeddings | - | 1-3 天 | 0.5-2 天 |

总体训练时间：

```text
CPU 预处理: 2-4 天并行
GPU 主训练: 6-14 天（4 GPU 推荐）
下游评测: 2-5 天
第一版完整周期: 10-23 天
```

## 9. 下游任务设计

必须做正式 benchmark，不做玩具验证。

### 9.1 单碱基/区域标注任务

| 任务 | 标签来源 | 指标 |
|---|---|---|
| CDS/exon/intron/UTR/intergenic segmentation | GFF/GTF | per-base F1, MCC, AUROC |
| splice donor/acceptor | exon-intron junction | AUPRC, F1, top-k recall |
| start/stop codon window | CDS | F1, MCC |
| promoter/TSS proxy | GFF/GTF TSS upstream | AUROC, AUPRC |
| TES/polyA proxy | TES flank | AUROC, AUPRC |

### 9.2 跨物种泛化

训练在部分属，测试留出属：

```text
Arabidopsis -> Brassica
Brassica -> Arabidopsis/Capsella/Cardamine
Brassica/Arabidopsis -> Thlaspi/Noccaea
```

指标：

```text
macro F1
cross-genus AUROC
performance drop vs in-genus validation
```

### 9.3 Brassica 专项任务

1. B. napus / B. rapa / B. oleracea 序列分类。
2. polyploid B. napus A/C subgenome proxy 分类（若可由 chromosome naming 推断）。
3. gene-proximal TE/repeat vs non-repeat 识别。
4. homeologous gene flank embedding 相似性。

### 9.4 变异效应与保守性

优先任务：

```text
Arabidopsis known functional SNP/indel scoring
Brassica candidate variant zero-shot delta log-likelihood
cross-species conserved region retrieval
```

评估：

```text
delta MLM loss
embedding cosine shift
deleterious/common AUROC if labels available
```

### 9.5 基线模型

必须比较：

```text
one-hot CNN
DNABERT-2
Nucleotide Transformer v2
HyenaDNA
Caduceus / PlantCAD / PlantCAD2
AgroNT
```

对于下游任务，优先使用 mean token pooling，因为 2025 benchmark 显示 mean pooling 在多类序列分类中通常优于 summary token 和 max pooling。

## 10. 预期结果

合理预期：

1. 在十字花科 CDS/exon/intron/splice/TSS/TES 任务上超过通用 DNABERT-2/NT/HyenaDNA frozen embedding。
2. 在 Arabidopsis 与 Brassica 跨属转移上接近或超过 PlantCAD2 同规模模型，尤其在结构注释标签任务。
3. 对 B. napus polyploid/subgenome 相关序列差异形成可分 embedding。
4. 对 splice、start/stop、CDS frame 的监督头给出可解释的单碱基概率图。
5. 对表达/QTL 类任务不承诺零样本 SOTA，需结合表达、ATAC/ChIP 或变异标签做专门微调。

风险：

| 风险 | 影响 | 处理 |
|---|---|---|
| 结构注释仅 67 个 assembly | token 多样性有限 | 动态 mask、多 epoch、区域采样、后续扩展注释 |
| Brassica accession 过多且近重复 | 泄漏和过拟合 | duplicate group、assembly-level split、token cap |
| GFF/GTF 质量不一致 | 标签噪声 | 严格 parser QC、低置信标签降权 |
| TE/repeat annotation 不完整 | repeat 任务偏差 | 第一版只做 softmask/repeat proxy，不伪标无注释 repeat |
| 128K 训练显存压力 | stage D 失败 | 保留 64K 正式模型，128K 作为可选增强 |

## 11. 近期执行步骤

1. 生成 `data_manifests/brassicaceae_assemblies.tsv`。
2. 提交 FASTA QC 到 q07/q08。
3. 提交 GFF/GTF parse 到 q07/q08。
4. 建立 split 和 leakage check。
5. 建立 `sampling_index/region_candidates.parquet`。
6. 生成 Stage B transfer 数据。
7. 用户在 GPU 上运行 Stage B 正式训练。
8. 每完成一个小阶段，更新 `PROGRESS.md` 并推送 GitHub。

