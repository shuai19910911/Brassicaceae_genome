# BrassicaceaeGenomeFM 目录结构与文件说明

更新时间：2026-06-09 23:29:57 CST

本仓库只上传轻量说明、脚本、配置和小型 manifest。大体积训练数据保存在本地，并通过 `training_server_transfer/stage_b_bundle/` 或 `training_server_transfer/all_stages_bundle/` 统一搬运到训练服务器。

## GitHub 中的目录

### `data_manifests/`

- `brassicaceae_assemblies.tsv`：从 `/home/user/zhangzhishuai/data/plantDB/genome` 扫描得到的 220 个十字花科 assembly 总清单，包含 genome/annotation 路径、体积、是否有 genome、是否有 GFF/GTF、是否进入候选训练集。
- `brassicaceae_splits.tsv`：通过 FASTA QC 后进入正式 Stage B 的 66 个 assembly split。字段包含 assembly、species、genus、train/validation/test、pass contigs、pass bp。
- `region_candidates_4k_summary.tsv`：4K 候选窗口总数、split 分布、region 分布。
- `region_candidates_4k_by_assembly.tsv`：4K 候选窗口按 assembly/split/region 汇总。
- `region_candidates_8k_summary.tsv`：8K 候选窗口总数、split 分布、region 分布。
- `region_candidates_8k_by_assembly.tsv`：8K 候选窗口按 assembly/split/region 汇总。
- `region_candidates_16k_summary.tsv`：16K 候选窗口总数、split 分布、region 分布。
- `region_candidates_16k_by_assembly.tsv`：16K 候选窗口按 assembly/split/region 汇总。
- `region_candidates_32k_summary.tsv` / `region_candidates_32k_by_assembly.tsv`：32K 候选窗口汇总，用于 C1/C2/D 长上下文阶段。
- `region_candidates_64k_summary.tsv` / `region_candidates_64k_by_assembly.tsv`：64K 候选窗口汇总，用于 C2/D 长上下文阶段。
- `region_candidates_128k_summary.tsv` / `region_candidates_128k_by_assembly.tsv`：128K 候选窗口汇总，用于 D 长上下文阶段。
- `stage_b_sampling_plan.tsv`：Stage B 正式训练采样计划，目标 20B train tokens，包含每个 region 的可用窗口数、目标窗口数、目标 token 数和采样比例。
- `stage_b_token_shard_plan.tsv`：GPU-ready token shard 生成计划，记录每个 split/context/region 在 12 个输出 shard 中的可用窗口和目标窗口。
- `stage_c1_sampling_plan.tsv` / `stage_c1_token_shard_plan.tsv`：Stage C1 8K/16K/32K 正式采样与 token shard 计划。
- `stage_c2_sampling_plan.tsv` / `stage_c2_token_shard_plan.tsv`：Stage C2 8K/32K/64K 正式采样与 token shard 计划。
- `stage_d_sampling_plan.tsv` / `stage_d_token_shard_plan.tsv`：Stage D 32K/64K/128K 正式采样与 token shard 计划。

### `configs/`

- `stage_b_data.yaml`：训练服务器读取数据的主配置。指向 bundle 内 manifest、FASTA QC、annotation QC、4K/8K/16K candidate shard 和动态 masking/RC 设置。
- `all_stages_data.yaml`：B/C1/C2/D 全阶段 token shard 配置，训练端优先读取各阶段 `stage_*_token_shards/summary.json` 与 `manifest.tsv`。

### `scripts/`

- `build_manifest.py`：扫描原始 genome 目录，生成 assembly 总清单。
- `fasta_qc.py`：流式读取 `.fna.gz`，生成 contig-level QC、assembly QC 和 checksum shard。
- `parse_annotations.py`：解析 GFF/GTF，生成 feature shard 和 intron shard。
- `merge_qc_shards.py`：合并 FASTA QC 的小型 shard。
- `recompute_fasta_qc.py`：从已合并 contig 表重算 FASTA pass/fail，不重扫 FASTA。
- `build_splits.py`：基于 manifest 和 assembly QC 生成 deterministic assembly-level split。
- `summarize_annotation_qc.py`：流式扫描 annotation shard，生成 feature summary 和 coordinate QC。
- `build_region_candidates.py`：按 4K/8K/16K context 生成 region-aware candidate window shard。
- `summarize_region_candidates.py`：统计 candidate shard 的 split/region/assembly 分布。
- `build_stage_b_sampling_plan.py`：根据 candidate summary 生成 Stage B 20B token 采样计划。
- `build_stage_b_token_shard_plan.py`：根据 candidate owner 分布生成 per-shard token materialization 计划。
- `build_stage_b_token_shards.py`：按 shard plan 从 FASTA 提取序列并写出 GPU-ready `uint8` token shard。
- `summarize_stage_b_token_shards.py`：汇总 token shard 的窗口数、token 数和文件清单。
- `create_stage_b_transfer_bundle.py`：生成训练服务器搬运用单目录 bundle。
- `build_stage_transfer_bundle.py`：生成包含 B/C1/C2/D 全阶段数据的训练服务器搬运用单目录 bundle。

### `slurm/`

- `run_fasta_qc_shard.sh`：q07 FASTA QC array 脚本。
- `run_annotation_parse_shard.sh`：q08 annotation parse array 脚本。
- `run_annotation_qc_summary.sh`：annotation 坐标 QC 汇总脚本。
- `run_region_candidates_4k.sh`：生成 4K candidate window shard。
- `run_region_candidates_8k.sh`：生成 8K candidate window shard。
- `run_region_candidates_16k.sh`：生成 16K candidate window shard。
- `run_stage_b_token_shards.sh`：生成 Stage B GPU-ready token shard；使用 `python3` 标准库直接运行，不依赖 `mamba run`。
- `run_region_candidates_context.sh`：按环境变量生成 32K/64K/128K 等长上下文 candidate window shard。
- `run_stage_b_token_shards.sh`：同一脚本通过 `STAGE_NAME`、`SAMPLING_PLAN`、`SHARD_PLAN`、`OUT_DIR` 等环境变量复用生成 C1/C2/D token shard。

### 项目根目录文档

- `README.md`：项目入口说明。
- `PROJECT_PLAN.md`：完整训练计划。
- `MODEL_STRUCTURE.md`：模型结构解析。
- `PROGRESS.md`：唯一主要进展文件，每条含具体更新时间。
- `TRANSFER_MANIFEST.md`：训练服务器搬运说明，生成 bundle 后同步更新。

## 本地大数据目录

这些目录默认不上传 GitHub。

### `sequence_index/`

- `contigs.tsv`：202,346 条 contig 级 QC 记录，包含长度、GC、N fraction、max N run、pass_qc。
- `assembly_qc.tsv`：67 个结构注释可用 assembly 的 FASTA QC 汇总；66 个通过，1 个因高 N fraction 排除。
- `fasta_checksums.tsv`：67 个 genome FASTA 的 SHA256。
- `*.shard*.tsv`：上述表的中间 shard，可保留用于审计，训练搬运不必须。

### `annotation_index/`

- `features.shard00.tsv`、`features.shard01.tsv`、`features.shard02.tsv`：GFF/GTF 解析得到的 gene/mRNA/exon/CDS/UTR feature shard。
- `introns.shard00.tsv`、`introns.shard01.tsv`、`introns.shard02.tsv`：由 exon chain 推断的 intron shard。
- `annotation_feature_summary.tsv`：各 assembly 各 feature 类型数量汇总。
- `annotation_coordinate_qc.tsv`：坐标合法性 QC；53,274,482 行中 23 行异常。

Stage B 训练只需要 `annotation_feature_summary.tsv` 和 `annotation_coordinate_qc.tsv` 做审计；完整 feature/intron shard 只有在训练服务器上重建候选窗口或扩展 C1/C2/D 时才需要搬。

### `sampling_index/`

- `region_candidates_4k.shard00.tsv`、`shard01.tsv`、`shard02.tsv`：4K Stage B 候选窗口坐标。
- `region_candidates_8k.shard00.tsv`、`shard01.tsv`、`shard02.tsv`：8K Stage B 候选窗口坐标。
- `region_candidates_16k.shard00.tsv`、`shard01.tsv`、`shard02.tsv`：16K Stage B 候选窗口坐标。
- `region_candidates_32k.shard00.tsv`、`shard01.tsv`、`shard02.tsv`：32K 长上下文候选窗口坐标。
- `region_candidates_64k.shard00.tsv`、`shard01.tsv`、`shard02.tsv`：64K 长上下文候选窗口坐标。
- `region_candidates_128k.shard00.tsv`、`shard01.tsv`、`shard02.tsv`：128K 长上下文候选窗口坐标。

这些 candidate 文件是审计/重建用坐标索引。正式训练优先读取 `stage_*_token_shards/` 中已展开的 `uint8` token shard。

### `training_server_transfer/stage_b_bundle/`

这是最终搬运目录。训练服务器不能访问原始 genome 目录时，只搬运这个目录即可。

当前 bundle 验收结果：

- 总大小：约 43G。
- `raw_genomes_manifest.tsv`：67 行，含表头，对应 66 个 raw genome FASTA。
- `TRANSFER_FILES.tsv`：194 行，含表头，对应 193 个 bundle 文件。
- `sampling_index/`：4K、8K、16K 各 3 个 candidate shard。
- `data_manifests/stage_b_sampling_plan.tsv`：34 行，含表头，覆盖 4K/8K/16K 的 train、validation、test 采样计划。
- `stage_b_token_shards/`：GPU-ready `uint8` token shard，训练服务器可直接 mmap 读取。

### `training_server_transfer/all_stages_bundle/`

这是全阶段搬运目录。训练服务器存储够大时，优先搬运这个目录。

当前 bundle 验收结果：

- 总大小：约 125G。
- `raw_genomes_manifest.tsv`：67 行，含表头，对应 66 个 raw genome FASTA。
- `TRANSFER_FILES.tsv`：480 行，含表头，对应 479 个 bundle 文件。
- `sampling_index/`：4K、8K、16K、32K、64K、128K 各 3 个 candidate shard。
- `stage_b_token_shards/`：B 阶段 GPU-ready token shard，train 19,999,989,760 tokens。
- `stage_c1_token_shards/`：C1 阶段 GPU-ready token shard，train 19,995,648,000 tokens。
- `stage_c2_token_shards/`：C2 阶段 GPU-ready token shard，train 9,999,958,016 tokens。
- `stage_d_token_shards/`：D 阶段 GPU-ready token shard，train 3,999,956,992 tokens。

### `stage_b_token_shards/`、`stage_c1_token_shards/`、`stage_c2_token_shards/`、`stage_d_token_shards/`

- `train_00000.bin` 到 `train_00011.bin`：训练 token 二进制 shard，`uint8` 编码，A=0、C=1、G=2、T=3、N/其他=4。
- `train_00000.idx.tsv` 到 `train_00011.idx.tsv`：训练 shard 索引，记录每条 window 在 `.bin` 中的 byte offset、length、assembly、seq、start/end、context 和 region。
- `validation_*.bin/.idx.tsv`：validation GPU-ready token shard。
- `test_*.bin/.idx.tsv`：test GPU-ready token shard。
- `shard_*.stats.json`：每个输出 shard 的窗口数和 token 数。
- `manifest.tsv`：全部 `.bin/.idx.tsv` 文件清单。
- `summary.json`：全局 token/window 汇总；训练端应以该文件记录的实际 token/window 数为准。
