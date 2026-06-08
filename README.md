# Brassicaceae_genome

更新时间：2026-06-08 23:16:12 CST

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

第一版正式预训练只使用 67 个同时具备 genome FASTA 和结构注释的 assembly。153 个暂无结构注释的 genome 不进入第一版主训练，后续可作为 genome-only continual pretraining 或对比扩展集。

## 文档

- [完整训练计划](PROJECT_PLAN.md)
- [模型结构解析](MODEL_STRUCTURE.md)
- [项目进展](PROGRESS.md)

## GitHub 仓库范围

GitHub 只保存项目介绍、计划、模型结构解析和主要进展。以下内容不上传 GitHub：

- 原始 FASTA/GFF/GTF 数据
- 预处理后的大体积索引和 stage input
- GPU checkpoint
- 下游任务大结果文件
- 临时日志和 debug 文件

