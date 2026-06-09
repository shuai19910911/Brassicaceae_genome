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

## 2026-06-09 10:54:05 CST

- 将 annotation 坐标 QC 从 q07 pending job `8469612` 取消后改投 q08；高资源 pending job `8469620` 也取消，低资源 job `8469622` 使用 8 CPU/32 GB 成功完成。该任务流式扫描 53,274,482 行，输出 `annotation_index/annotation_feature_summary.tsv` 和 `annotation_index/annotation_coordinate_qc.tsv`。
- Annotation 坐标 QC 结果：总 invalid coordinate 23 行，invalid fraction 0.00000043，可在后续候选窗口构建时过滤，不影响进入 sampling index 阶段。
- 已生成 8K region-aware 候选窗口，SLURM array job `8469629` 三个 shard 均成功完成，输出到 `sampling_index/region_candidates_8k.shard00.tsv`、`shard01.tsv`、`shard02.tsv`。
- Region candidate 总量为 30,757,136 个 8K 窗口；split 分布为 train 23,995,104、validation 4,311,272、test 2,450,760；region 分布以 CDS 15,090,276、intron 8,465,378、exon 3,731,972 为主，background 417,004。
- 已生成 Stage B 正式采样计划 `data_manifests/stage_b_sampling_plan.tsv`：目标 train tokens 20B，对应 2,441,406 个 8K 窗口；validation/test 各抽 50,000 个 8K 窗口用于阶段性评估。
- 已新增 Stage B 数据配置 `configs/stage_b_data.yaml`，训练端应按 sharded candidate + dynamic masking + dynamic reverse-complement 读取，不合并大 candidate 表，也不提前固化 mask。

## 2026-06-09 13:29:03 CST

- 已按正式 Stage B 多上下文口径补齐 4K、8K、16K region-aware candidate window。4K/16K 初始失败或排队分片已转投 `cu` 分区，补跑 job `8469834`、`8469835`、`8469836` 均成功完成。
- 当前 `sampling_index/` 共 9 个 candidate shard：4K、8K、16K 各 3 个。窗口总量为 92,400,506 个候选窗口（不含各 shard 表头）；其中 4K 31,233,223 个、8K 30,757,136 个、16K 30,410,147 个。
- 已重新生成 `data_manifests/stage_b_sampling_plan.tsv`，正式 Stage B 训练目标为 20B train tokens，采用 4K/8K/16K 混合上下文；validation/test 在每个 context 各保留 50,000 个窗口用于阶段性评估。
- 已创建训练服务器单目录搬运包：`training_server_transfer/stage_b_bundle/`。该目录当前约 21G，包含 66 个通过 QC 并进入 split 的 raw genome FASTA、9 个 sampling candidate shard、FASTA QC、annotation summary/QC、训练配置、数据 manifest、处理脚本和文件清单。
- 训练服务器不能访问 `/home/user/zhangzhishuai/data/plantDB/genome`，因此搬运时只需要搬运 `training_server_transfer/stage_b_bundle/` 这一个目录；其中 `raw_genomes/` 已包含训练端读取候选坐标所需的原始 `.fna.gz`。
- 已新增 `DIRECTORY_STRUCTURE.md` 和 `TRANSFER_MANIFEST.md`，分别说明 GitHub/本地/bundle 目录结构、每个文件用途，以及训练服务器搬运命令和边界。

## 2026-06-09 17:14:06 CST

- 回答并落实 GPU 训练吞吐问题：不再建议训练时直接从 `.fna.gz` 按坐标反复抽序列；已在当前 CPU/SLURM 服务器预生成 GPU-ready `uint8` token shard，训练服务器可直接 mmap 读取。
- 新增并运行 Stage B token materialization 流程：`scripts/build_stage_b_token_shard_plan.py`、`scripts/build_stage_b_token_shards.py`、`scripts/summarize_stage_b_token_shards.py` 和 `slurm/run_stage_b_token_shards.sh`。
- 修正采样计划生成逻辑：train region 可用数改为从 `region_candidates_*_by_assembly.tsv` 统计 train-only count，避免把 validation/test 的 region 窗口误计入 train；稀有 region 不足时自动回填到其他有容量 region。
- 已生成 `data_manifests/stage_b_token_shard_plan.tsv`，按 12 个 owner shard 分配采样目标；核验结果为 train 2,807,616 windows、19,999,989,760 tokens，且无 shard 超过可用窗口。
- 最终 token shard job `8470518` 已在 `cu` 分区完成，12 个 array 分片均 `COMPLETED`；最大 RSS 约 396-492 MB/分片，单分片耗时约 14:49-16:04。
- `stage_b_token_shards/` 已生成并汇总：train 19,999,989,760 tokens、2,807,616 windows；validation 1,433,600,000 tokens、150,000 windows；test 1,433,600,000 tokens、150,000 windows。目录大小约 22G。
- 已刷新 `training_server_transfer/stage_b_bundle/`，将 GPU-ready token shards 纳入同一个搬运目录；当前 bundle 约 43G，`TRANSFER_FILES.tsv` 194 行，含表头，对应 193 个 bundle 文件。

## 2026-06-09 23:29:57 CST

- 按用户要求补齐所有训练阶段数据，使训练服务器存储足够时可以一次性搬运多阶段数据；GPU 训练端不需要访问登录节点原始 genome 目录。
- 已生成长上下文 region-aware candidate window：32K 共 30,061,578 个候选窗口，64K 共 29,677,881 个候选窗口，128K 共 29,240,062 个候选窗口；每个 context 均为 3 个 shard。
- 已生成 C1/C2/D 采样计划与 per-shard token materialization 计划：C1 目标 20B train tokens，8K/16K/32K 混合；C2 目标 10B train tokens，8K/32K/64K 混合；D 目标 4B train tokens，32K/64K/128K 混合。
- Stage C1 token shard job `8529096` 已完成，12 个 array 分片均 `COMPLETED`；`stage_c1_token_shards/` 约 25G，train 19,995,648,000 tokens、1,037,361 windows，validation/test 各 2,867,200,000 tokens、150,000 windows。C1 少量短缺来自 `train|32768|transcript` 候选不足，脚本已记录 `shortfalls`，不是任务失败。
- Stage C2 token shard job `8529098` 已完成，12 个 array 分片均 `COMPLETED`；`stage_c2_token_shards/` 约 20G，train 9,999,958,016 tokens、289,916 windows，validation/test 各 5,324,800,000 tokens、150,000 windows。
- Stage D token shard job `8529097` 已完成，12 个 array 分片均 `COMPLETED`；`stage_d_token_shards/` 约 26G，train 3,999,956,992 tokens、45,776 windows，validation/test 各 11,468,800,000 tokens、150,000 windows。
- 已生成全阶段训练服务器搬运包：`training_server_transfer/all_stages_bundle/`，约 125G，包含 66 个 raw genome FASTA、4K/8K/16K/32K/64K/128K candidate shard、B/C1/C2/D GPU-ready token shard、manifest、配置、脚本和说明文档；`TRANSFER_FILES.tsv` 480 行，含表头，对应 479 个文件；未生成 `MISSING_PATTERNS.txt`，说明必需模式均已找到。
