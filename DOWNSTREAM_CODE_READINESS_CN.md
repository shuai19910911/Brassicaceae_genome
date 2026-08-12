# 下游代码准备状态

## 结论

下游代码框架已经覆盖`DOWNSTREAM_TASKS.md`中的26项任务，但当前没有任何正式下游数据release，因此状态是`CODE_READY_DATA_NOT_FROZEN`，不是“下游实验已完成”。

## 已实现

- 任务registry：P1–P7、P2B、B1–B12、X1–X6，无静默遗漏。
- 方法矩阵：每个任务×方法单元明确标记ready、blocked或not applicable。
- 输入适配：FASTA/FASTA.GZ、CSV、TSV、pair、0-based half-open coordinate和GFF3。
- DNA规范化：ACGTN；IUPAC歧义码映射N；非法符号拒绝。
- 泄漏检查：样本ID、正反链等价序列、biological group和跨split坐标重叠。
- 简单基线：majority/prevalence、GC+length、1/3/6-mer、random ranking。
- 指标：AUPRC、MCC、macro-F1、校准、Spearman、Pearson、R²、MAE、MRR、Recall@K和multi-label segmentation。
- 统计：最高层独立cluster bootstrap、paired permutation。
- 正式评估：固定train/validation/test；5 seed；validation选择；test只报告；每seed测试访问次数明确记录。
- 正式数据release：`samples.jsonl`、`manifest.json`、`receipt.json`、`READY`组成exact-file closure；目录0555、文件0444、registry hash和数据root hash双重绑定。
- runner只接受通过上述校验的不可变release路径；已删除可凭自报dataset hash把任意内存样本发布成PASS的正式入口。
- Brassi frozen encoder：复用正式checkpoint envelope/root hash验证、DDP键归一化、单碱基token化、128K pooled embedding、singleton/pair特征。
- 外部模型：local-only、`trust_remote_code=False`的通用HuggingFace adapter已实现；缺模型专属兼容验证、不可变revision或本地权重回执的方法保持blocked。
- 统一CLI：`workspace/code/run_downstream.py --status`列出完整registry；执行时必须给task、method、不可变dataset release和输出目录；CUDA encoder另需显式授权短语。
- 结果release：`metrics.json`、`predictions.tsv`、`receipt.json`、`READY`，禁止覆盖。

## 当前真实blocker

缺少每项任务的正式数据、标签、不可拆分group和固定split release。代码不会因为文件名或相似任务自动猜标签，也不会把公开模型权重缺失伪装成零分。

只有在某项数据release至少具备以下内容后才能执行：

1. train/validation/test三份固定split；
2. 直接标签和来源元数据；
3. orthogroup/LD block/study/cultivar等最高层不可拆分单位；
4. 序列与坐标泄漏PASS回执；
5. 数据root hash；
6. 任务主指标和最小样本门槛。

## 主要代码

- `workspace/code/brassi_data/downstream_registry.py`
- `workspace/code/brassi_data/downstream_adapters.py`
- `workspace/code/brassi_data/downstream_dataset.py`
- `workspace/code/brassi_data/downstream_metrics.py`
- `workspace/code/brassi_data/downstream_runner.py`
- `workspace/code/brassi_data/downstream_models.py`
- `workspace/code/run_downstream.py`

本状态不启动GPU，也不读取预训练sealed test。
