# 训练服务器搬运说明

更新时间：2026-06-09 23:29:57 CST

训练服务器不能访问：

```text
/home/user/zhangzhishuai/data/plantDB/genome
```

因此不能只搬运坐标索引，必须把 66 个 split assembly 的原始 genome FASTA 一起放进搬运目录。

## 只需要搬运一个目录

如果只训练 Stage B，搬运：

```text
/home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel/training_server_transfer/stage_b_bundle
```

当前目录大小约 43G。

如果训练服务器存储足够，优先搬运全阶段目录：

```text
/home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel/training_server_transfer/all_stages_bundle
```

当前目录大小约 125G，包含 66 个 split assembly 的 raw genome FASTA、4K/8K/16K/32K/64K/128K 坐标索引、B/C1/C2/D GPU-ready token shard 和训练所需全部轻量/中量索引。搬运时不要只搬 `sampling_index/`，因为训练服务器不能访问登录节点上的原始 genome 目录。

搬运到训练服务器后，训练代码应以该目录作为数据根目录。建议目标路径例如：

```text
/data/BrassicaceaeGenomeFM/all_stages_bundle
```

## Bundle 内部结构

```text
all_stages_bundle/
  TRANSFER_FILES.tsv
  raw_genomes_manifest.tsv
  raw_genomes/
  configs/
  data_manifests/
  sequence_index/
  annotation_index/
  sampling_index/
  stage_b_token_shards/
  stage_c1_token_shards/
  stage_c2_token_shards/
  stage_d_token_shards/
  scripts/
```

### `raw_genomes/`

66 个通过 QC 并进入 split 的 assembly 原始 `.fna.gz`。训练服务器不能访问原始 genome 目录时，这是必需目录。

### `raw_genomes_manifest.tsv`

记录每个 assembly 的原始路径、bundle 内相对路径和字节数。训练端可用此表建立 assembly_id 到 FASTA 的映射。

### `configs/stage_b_data.yaml` 和 `configs/all_stages_data.yaml`

`stage_b_data.yaml` 是 Stage B 训练主配置。`all_stages_data.yaml` 是全阶段配置。训练代码应将其中路径解析为 bundle 内相对路径，并优先使用 token shard：

```text
stage_b_token_shards/
stage_c1_token_shards/
stage_c2_token_shards/
stage_d_token_shards/
```

### `data_manifests/`

小型训练元数据、split、candidate summary 和 Stage B 采样计划。

### `sequence_index/`

FASTA QC 和 checksum。训练前应至少检查：

```text
assembly_qc.tsv
fasta_checksums.tsv
contigs.tsv
```

### `annotation_index/`

只放 Stage B 训练审计所需的小型 summary/QC：

```text
annotation_feature_summary.tsv
annotation_coordinate_qc.tsv
```

完整 feature/intron shard 不放入默认 bundle，避免不必要搬运 12G；当前 all-stages bundle 已经包含全部候选窗口和 token shard，训练不需要重建 candidate。

### `sampling_index/`

正式训练候选窗口坐标：

```text
region_candidates_4k.shard*.tsv
region_candidates_8k.shard*.tsv
region_candidates_16k.shard*.tsv
region_candidates_32k.shard*.tsv
region_candidates_64k.shard*.tsv
region_candidates_128k.shard*.tsv
```

这些不是测试数据，也不是 toy subset。它们覆盖 66 个正式 split assembly。训练优先读取已经展开的 `stage_*_token_shards/`；`sampling_index/` 主要用于审计和重建。

### `stage_*_token_shards/`

正式训练优先使用这些目录，而不是训练时实时解压 FASTA。每个目录包含已按采样计划提取好的 `uint8` token：

```text
train_00000.bin ... train_00011.bin
train_00000.idx.tsv ... train_00011.idx.tsv
validation_*.bin / validation_*.idx.tsv
test_*.bin / test_*.idx.tsv
manifest.tsv
summary.json
```

token 编码为 A=0、C=1、G=2、T=3、N/其他=4。训练端应 mmap `.bin`，按 `.idx.tsv` 的 offset/length 切片；dynamic masking 和 reverse-complement augmentation 仍在训练时做，不需要固化到 shard。

当前实际 token 汇总：

| 阶段 | 上下文 | train tokens | validation tokens | test tokens | 本地目录大小 |
|---|---|---:|---:|---:|---:|
| B | 4K/8K/16K | 19,999,989,760 | 1,433,600,000 | 1,433,600,000 | 22G |
| C1 | 8K/16K/32K | 19,995,648,000 | 2,867,200,000 | 2,867,200,000 | 25G |
| C2 | 8K/32K/64K | 9,999,958,016 | 5,324,800,000 | 5,324,800,000 | 20G |
| D | 32K/64K/128K | 3,999,956,992 | 11,468,800,000 | 11,468,800,000 | 26G |

### `scripts/`

保留生成和审计数据的脚本，方便训练服务器上复查。

### `TRANSFER_FILES.tsv`

bundle 内所有文件列表和字节数。搬运后可用它核对文件完整性。

## 搬运命令示例

推荐使用 `rsync`：

```bash
rsync -avh --info=progress2 \
  /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel/training_server_transfer/all_stages_bundle/ \
  USER@TRAIN_SERVER:/data/BrassicaceaeGenomeFM/all_stages_bundle/
```

也可以先打包：

```bash
tar -C /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel/training_server_transfer \
  -czf BrassicaceaeGenomeFM_all_stages_bundle.tar.gz all_stages_bundle
```

由于 bundle 内包含大体积 FASTA 和 sampling index，打包可能耗时较长；`rsync` 更稳。

## 当前阶段边界

`all_stages_bundle/` 支持 B/C1/C2/D 正式训练。训练时优先读取 `stage_*_token_shards/`；`raw_genomes/` 和 `sampling_index/` 保留用于审计、复现和后续重建。
