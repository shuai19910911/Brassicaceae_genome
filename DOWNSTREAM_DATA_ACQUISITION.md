# 下游任务数据获取清单（外部实验数据）

本清单列出无法从本地 plantDB 基因组/GFF 或 NC 基准 zip 直接派生、
需要外部实验数据的任务。每个任务给出确切来源、获取路径和当前状态。
状态说明：
- READY：数据 release 已冻结（本地派生或已下载转换）
- ACQUIRING：正在下载/处理
- BLOCKED_PENDING_DATA：需要外部数据下载，来源已核实，可随时执行
- INFEASIBLE_FOR_CONFIRMATORY：无公开可靠数据，不能进入确认性分析

## 状态总表

| 任务 | 数据来源 | 状态 |
|------|----------|------|
| P1 coding/intergenic | plantDB 本地 GFF 派生 | READY（release 已冻结） |
| P3 splice donor/acceptor | plantDB 本地 GFF 派生 | READY（release 已冻结） |
| P4 region type 4类 | plantDB 本地 GFF 派生 | READY（release 已冻结） |
| P8 4mC 拟南芥+Geum×2 | NC 基准 zip（HF hfeng3/dna_foundation_benchmark_dataset） | READY（release 已冻结） |
| P10a 十字花科内物种分类 | plantDB 本地（4 物种×全部 split） | READY（release 已冻结） |
| P10b 十字花科 vs 外群 | plantDB 本地（番茄/水稻/玉米/黄瓜） | READY（release 已冻结） |
| P13a iPro-WAEL TATA/NonTATA | NC 基准 zip | READY（release 已冻结） |
| P13b 核心启动子 70bp | plantDB 本地 GFF 派生 | READY（release 已冻结） |
| P13c 启动子 300bp | plantDB 本地 GFF 派生 | READY（release 已冻结） |
| P5 DNA→表达 | SRA：拟南芥 PRJNA381569 等 tissue RNA-seq；或 PlantCAD2/AgroNT 附带表达集 | BLOCKED_PENDING_DATA |
| P6 长程调控 | PlantCAD2 公开任务数据（kuleshov-group HF collection） | BLOCKED_PENDING_DATA |
| P7 变异效应 | songlab/gpn-brassicales 配套 VCF/注释；At 1001 Genomes VCF | BLOCKED_PENDING_DATA |
| P9 DNase/ATAC 开放染色质 | GEO GSE53322（At DNase-seq）；PlantDHS（plantdhs.org）BED | BLOCKED_PENDING_DATA |
| P11 增强子/STARR-seq | GEO GSE144826（Jores et al. 2020 At STARR-seq） | BLOCKED_PENDING_DATA |
| P12 TAD 边界 | GEO GSE96418（Liu et al. 2017 At Hi-C） | BLOCKED_PENDING_DATA |
| B1–B12 十字花科专属 | 论文/BIGD/Ensembl Plants 来源，需逐任务核实 | BLOCKED_PENDING_DATA |

## 公共模型权重缓存状态

| 模型 | 仓库 | 状态 |
|------|------|------|
| AgroNT 1B | InstaDeepAI/agro-nucleotide-transformer-1b | READY（down_model/AgroNT_1B） |
| DNABERT-2 117M | zhihan1996/DNABERT-2-117M | READY（down_model/DNABERT2） |
| NT v2 500M multi-species | InstaDeepAI/nucleotide-transformer-v2-500m-multi-species | READY（down_model/NTv2_500M_multi_species） |
| HyenaDNA medium 160K | LongSafari/hyenadna-medium-160k-seqlen-hf | READY（down_model/HyenaDNA_medium_160k） |
| GPN-Brassicales | songlab/gpn-brassicales | READY（down_model/GPN_Brassicales） |
| PlantCAD2-M/L | kuleshov-group | READY（down_model/PlantCAD2_Small、PlantCAD2_Large） |
| PlantCaduceus | PNAS 10.1073/pnas.2421738122 | READY（down_model/PlantCaduceus_l32） |
| Caduceus-PS | 植物噬菌体基准 | READY（down_model/Caduceus_Ph_131k_d_model256） |
| Evo 2 1B | Arc Institute | READY（down_model/Evo2_1B_base） |
| 其他备用基线 | — | READY（GENA_LM_BERT_base、PlantBiMoE、PlantDNAMamba_BPE、PlantNT_singlebase） |

## 数据获取的下一步（等用户确认执行）

1. SRA/GEO 下载（P5/P9/P11/P12）：约 20-60 GB 原始数据，需在 q03 或存储节点
   用 sra-tools/fasterq-dump 处理；峰值与耗时较大，属于"重活"。
2. PlantCAD2 权重：向 kuleshov-group 邮件/HF collection 核实公开链接后下载。
3. B 系列十字花科专属数据：按 B1-B12 设计文档逐任务从指定论文补充材料获取。
