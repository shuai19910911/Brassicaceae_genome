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

