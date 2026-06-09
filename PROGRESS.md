# BrassicaceaeGenomeFM 项目进展

本文件作为唯一主要进展文件。每条进展必须包含具体更新时间点，避免分散生成大量进展文档。

## 2026-06-08 23:16:12 CST

- 建立项目正式口径：第一版训练 `BrassicaceaeGenomeFM-330M`，采用结构注释驱动、单碱基 token、bidirectional Mamba/Caduceus 风格 backbone、reverse-complement 一致性、多任务结构监督和长上下文 curriculum。
- 完成本地数据初步盘点：`/home/user/zhangzhishuai/data/plantDB/genome` 中十字花科候选 assembly 220 个，均有 genome FASTA；其中 67 个同时具备 genome FASTA 与 GFF/GTF 结构注释。
- 统计 67 个注释可用 assembly 的压缩 genome 合计 8.22 GB，压缩结构注释合计 0.86 GB。
- 确定第一版正式训练只使用 67 个结构注释可用 assembly；153 个暂无结构注释的 genome 暂不混入主训练，后续作为 genome-only continual pretraining 或扩展注释数据。
- 参考并吸收已有 `douke_genome` 与 `zuowu_genomemodel` 项目策略：GitHub 只保存 README、计划、模型结构解析和主要进展；大数据、stage input、checkpoint 和临时日志不上传。
- 完成文献与前沿路线调研，纳入 Nucleotide Transformer、DNABERT-2、HyenaDNA、Caduceus、PlantCAD/PlantCaduceus、GPN、SegmentNT、AgroNT 和 2025 DNA foundation model benchmark 的设计启发。
- 生成项目入口 README、完整训练计划 `PROJECT_PLAN.md` 和模型结构解析 `MODEL_STRUCTURE.md`。

## 2026-06-09 09:29:34 CST

- 开始第一轮正式数据处理。新增可复用处理脚本：`scripts/build_manifest.py`、`scripts/fasta_qc.py`、`scripts/parse_annotations.py`，以及 SLURM array 提交脚本 `slurm/run_fasta_qc_shard.sh`、`slurm/run_annotation_parse_shard.sh`。
- 已生成 manifest：`data_manifests/brassicaceae_assemblies.tsv`，共 220 个十字花科 assembly 记录，其中 67 个 `train_eligible=1`，与 2026-06-08 数据盘点一致。
- 已提交 GFF/GTF 结构注释解析 array job：`8469414`，分区 `q08`，array `0-2`，每个 shard 申请 30 CPU 和 150 GB 内存，输出到 `annotation_index/features.shard*.tsv` 与 `annotation_index/introns.shard*.tsv`。
- 已提交 FASTA 流式 QC array job：`8469415`，分区 `q07`，array `0-2`，每个 shard 申请 30 CPU 和 150 GB 内存，输出到 `sequence_index/contigs.shard*.tsv`、`sequence_index/assembly_qc.shard*.tsv` 与 `sequence_index/fasta_checksums.shard*.tsv`。
- 当前 SLURM 状态：两个 array job 均已进入队列，状态为 `PD (Resources)`，等待计算节点资源。

## 2026-06-09 09:36:33 CST

- 发现原 FASTA QC shard `8469415_0` 在 `mamba run` 启动阶段失败，错误为 libmamba JSON parse error，未进入 FASTA 数据处理主体，也未产生 shard 0 结果表。
- 已仅补交失败 shard：`8469433_0`，分区 `q07`，申请 30 CPU 和 150 GB 内存。当前 `8469433_0` 已在 `cu16` 运行。
- 当前运行状态：FASTA QC shard `8469415_1`、`8469415_2`、`8469433_0` 均在运行；annotation parse shard `8469414_0`、`8469414_1` 在运行，`8469414_2` 等待资源。

## 2026-06-09 10:12:51 CST

- 第一轮 FASTA QC 与 GFF/GTF annotation parse 已完成。Annotation parse 三个 shard 均成功完成；FASTA QC 原 shard `8469415_0` 启动失败，但补交 shard `8469433_0` 已成功完成。
- 已合并 FASTA QC 小表：`sequence_index/contigs.tsv` 共 202,346 条 contig 记录，`sequence_index/assembly_qc.tsv` 共 67 个 assembly 记录，`sequence_index/fasta_checksums.tsv` 共 67 个 checksum 记录。
- 修正 FASTA QC 规则：连续 N run `>=5 kb` 只作为后续窗口切分断点，不再作为整条 contig 失败条件；整条 contig 主 QC 条件保留为 length、N fraction 与核基因组/未知分类。修正后 67 个结构注释可用 assembly 中 66 个通过 FASTA QC。
- 当前唯一排除的结构注释可用 assembly 是 `Arabis_nemorensis_GCA_902206195.3`，原因是各 chromosome-level contig 的 N fraction 约 17.8%-21.5%，超过第一版主训练阈值 10%。
- 已生成正式 assembly-level split：`data_manifests/brassicaceae_splits.tsv`，共 66 个 assembly；train 53、validation 8、test 5。
- 已提交流式 annotation 坐标 QC 汇总任务 `8469612`，当前状态为 `PD (Resources)`，等待 q07 资源；该任务将输出 `annotation_index/annotation_feature_summary.tsv` 和 `annotation_index/annotation_coordinate_qc.tsv`。
