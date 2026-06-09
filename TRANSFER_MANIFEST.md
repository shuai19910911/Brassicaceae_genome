# Stage B 训练服务器搬运说明

更新时间：2026-06-09 13:29:03 CST

训练服务器不能访问：

```text
/home/user/zhangzhishuai/data/plantDB/genome
```

因此不能只搬运坐标索引，必须把 66 个 split assembly 的原始 genome FASTA 一起放进搬运目录。

## 只需要搬运一个目录

最终搬运目录：

```text
/home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel/training_server_transfer/stage_b_bundle
```

当前目录大小约 21G，包含 66 个 split assembly 的 raw genome FASTA 和 Stage B 训练所需全部轻量/中量索引。搬运时不要只搬 `sampling_index/`，因为训练服务器不能访问登录节点上的原始 genome 目录。

搬运到训练服务器后，训练代码应以该目录作为数据根目录。建议目标路径例如：

```text
/data/BrassicaceaeGenomeFM/stage_b_bundle
```

## Bundle 内部结构

```text
stage_b_bundle/
  TRANSFER_FILES.tsv
  raw_genomes_manifest.tsv
  raw_genomes/
  configs/
  data_manifests/
  sequence_index/
  annotation_index/
  sampling_index/
  scripts/
```

### `raw_genomes/`

66 个通过 QC 并进入 split 的 assembly 原始 `.fna.gz`。训练服务器不能访问原始 genome 目录时，这是必需目录。

### `raw_genomes_manifest.tsv`

记录每个 assembly 的原始路径、bundle 内相对路径和字节数。训练端可用此表建立 assembly_id 到 FASTA 的映射。

### `configs/stage_b_data.yaml`

Stage B 训练主配置。训练代码应将其中路径解析为 bundle 内相对路径，并使用：

```text
raw_genomes/
sampling_index/region_candidates_4k.shard*.tsv
sampling_index/region_candidates_8k.shard*.tsv
sampling_index/region_candidates_16k.shard*.tsv
data_manifests/stage_b_sampling_plan.tsv
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

完整 feature/intron shard 不放入默认 Stage B bundle，避免不必要搬运 12G；如果要在训练服务器上重建 candidate 或继续生成 C1/C2/D，再额外搬运本地 `annotation_index/features.shard*.tsv` 和 `annotation_index/introns.shard*.tsv`。

### `sampling_index/`

Stage B 正式训练候选窗口坐标：

```text
region_candidates_4k.shard*.tsv
region_candidates_8k.shard*.tsv
region_candidates_16k.shard*.tsv
```

这些不是测试数据，也不是 toy subset。它们覆盖 66 个正式 split assembly，并由动态 masking、动态 reverse-complement 和 region 权重在训练时采样。

### `scripts/`

保留生成和审计数据的脚本，方便训练服务器上复查。

### `TRANSFER_FILES.tsv`

bundle 内所有文件列表和字节数。搬运后可用它核对文件完整性。

## 搬运命令示例

推荐使用 `rsync`：

```bash
rsync -avh --info=progress2 \
  /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel/training_server_transfer/stage_b_bundle/ \
  USER@TRAIN_SERVER:/data/BrassicaceaeGenomeFM/stage_b_bundle/
```

也可以先打包：

```bash
tar -C /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel/training_server_transfer \
  -czf BrassicaceaeGenomeFM_stage_b_bundle.tar.gz stage_b_bundle
```

由于 bundle 内包含大体积 FASTA 和 sampling index，打包可能耗时较长；`rsync` 更稳。

## 当前阶段边界

该 bundle 支持 Stage B 正式训练：4K/8K/16K context mix、20B train tokens、validation/test 各 50,000 窗口。

尚未生成 C1/C2/D 的 32K/64K/128K candidate 和采样计划。如果要训练长上下文阶段，需要在 Stage B 后继续生成对应候选窗口或在训练服务器上用 annotation shard 重建。
