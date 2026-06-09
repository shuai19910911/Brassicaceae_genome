# Brassicaceae_genome

更新时间：2026-06-09 23:29:57 CST

BrassicaceaeGenomeFM 是面向十字花科（Brassicaceae）的结构注释驱动 DNA foundation model 项目。第一版目标不是测试版或玩具模型，而是直接按正式大模型训练口径准备：使用高质量 genome FASTA、GFF/GTF 结构注释、区域加权采样、长上下文 bidirectional Mamba/Caduceus 风格 backbone、reverse-complement 一致性训练和多任务结构监督。

## 当前正式口径

原始数据目录只读：

```text
/home/user/zhangzhishuai/data/plantDB/genome
```

本轮本地统计结果：

| 项目 | 数量/体积 |
|---|---:|
| 十字花科候选 assembly | 220 |
| 有 genome FASTA 的 assembly | 220 |
| 同时有 genome + GFF/GTF 的 assembly | 67 |
| 覆盖属 | 9 |
| 压缩 genome 体积（67 个注释可用 assembly） | 8.22 GB |
| 压缩结构注释体积（67 个注释可用 assembly） | 0.86 GB |

第一版正式预训练只使用结构注释可用 assembly。FASTA QC 后 66 个 assembly 进入 Stage B split；`Arabis_nemorensis_GCA_902206195.3` 因高 N fraction 被排除。153 个暂无结构注释的 genome 不进入第一版主训练，后续可作为 genome-only continual pretraining 或对比扩展集。

## 当前数据状态

所有已规划训练阶段的数据均已处理到可搬运状态：

- Stage B：4K/8K/16K，train 19,999,989,760 tokens，GPU-ready token shard 约 22G。
- Stage C1：8K/16K/32K，train 19,995,648,000 tokens，GPU-ready token shard 约 25G。
- Stage C2：8K/32K/64K，train 9,999,958,016 tokens，GPU-ready token shard 约 20G。
- Stage D：32K/64K/128K，train 3,999,956,992 tokens，GPU-ready token shard 约 26G。
- 4K/8K/16K/32K/64K/128K region-aware candidate window 均已生成，每个 context 3 个 shard。
- 训练服务器可直接 mmap 读取 `uint8` token shard，不需要训练时反复解压 FASTA。
- 如果只训练 Stage B，可搬运 `training_server_transfer/stage_b_bundle/`，约 43G。
- 如果训练服务器存储足够，优先搬运 `training_server_transfer/all_stages_bundle/`，约 125G，包含 raw genome、全部候选窗口、B/C1/C2/D token shard 和训练端所需配置/脚本/manifest。

## 文档

- [完整训练计划](PROJECT_PLAN.md)
- [模型结构解析](MODEL_STRUCTURE.md)
- [项目进展](PROGRESS.md)
- [目录结构与文件说明](DIRECTORY_STRUCTURE.md)
- [训练服务器搬运说明](TRANSFER_MANIFEST.md)

## GitHub 仓库范围

GitHub 只保存项目介绍、计划、模型结构解析和主要进展。以下内容不上传 GitHub：

- 原始 FASTA/GFF/GTF 数据
- 预处理后的大体积索引和 stage input
- GPU checkpoint
- 下游任务大结果文件
- 临时日志和 debug 文件
