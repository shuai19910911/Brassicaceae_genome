# BrassicaceaeGenomeFM 训练进展

## 0. 当前结论

截至 **2026-08-03 08:27:28 CST（UTC+08:00）**，项目已经完成旧项目清零、文献调研、最终设计、第二轮漏洞审计、无预定训练上限修订和综合Markdown/Word同步，但尚未开始新数据构建、模型编码、GPU训练或下游评测。

当前不是“模型训练完成”，也不是“数据准备完成”。所有尚未执行的科学结果统一记为 `N/A`，不能记成0或用计划值代替。

## 1. 状态矩阵

| 工作项 | 证据状态 | 执行状态 | 说明 |
|---|---|---|---|
| 旧项目本地内容清理 | VERIFIED | COMPLETE | 项目目录旧数据、旧shard、旧脚本、旧配置和旧文档已删除 |
| 外部原始数据保护 | VERIFIED | COMPLETE | `/home/user/zhangzhishuai/data/plantDB/genome` 位于项目外部且仍存在，未删除、未修改 |
| Nature Portfolio文献调研 | VERIFIED | COMPLETE | 检索冻结到2026-08-02；DOI/题名由Crossref、Europe PMC或Nature正式页核验 |
| 外部关键DNA模型调研 | VERIFIED | COMPLETE | AgroNT、PlantCAD2、PlantCaduceus、GPN、NT-v2和Evo 2的论文、权重、上下文与任务边界已核验并纳入设计 |
| 最终训练方案 | VERIFIED | FROZEN | 唯一文件 `TRAINING_PLAN.md` |
| 最终模型架构 | VERIFIED | FROZEN | 唯一文件 `MODEL_ARCHITECTURE.md` |
| 最终下游任务体系 | VERIFIED | FROZEN | 唯一文件 `DOWNSTREAM_TASKS.md` |
| 完整研究设计Markdown | VERIFIED | FROZEN | `BRASSICACEAE_GENOMEFM_COMPREHENSIVE_DESIGN.md`，自包含说明研究、数据、窗口、模型、训练、基线和20项下游任务 |
| 完整研究设计Word | VERIFIED | FROZEN | `BRASSICACEAE_GENOMEFM_COMPREHENSIVE_DESIGN.docx`，与Markdown正文一致；LibreOffice真实渲染为30页，含封面、静态实页码目录、页眉页脚和4个横向宽表 |
| 无预定训练上限修订 | VERIFIED | COMPLETE | 已取消54B/68,664步硬上限，改为coverage-cycle受控复用、四类token分账、冻结development门禁和WSD动态停止 |
| 第二轮训练设计漏洞审计 | VERIFIED | COMPLETE | 已补齐下游防火墙、混长归一化、显存、选择和checkpoint合同 |
| 新十字花科assembly清单 | UNKNOWN | NOT STARTED | 旧manifest作废；尚未重新做taxonomy和QC |
| 新split和近重复簇 | UNKNOWN | NOT STARTED | 尚无train/development/sealed test release |
| 新sequence/label store | UNKNOWN | NOT STARTED | 尚无新shard、标签或自包含bundle |
| 330M模型代码 | UNKNOWN | NOT STARTED | 当前只有冻结架构，无实现和单元测试结果 |
| 3×A100 40GB硬件验收 | UNKNOWN | NOT STARTED | 用户给定目标硬件；本次没有执行GPU任务 |
| 正式预训练 | UNKNOWN | NOT STARTED | 无run ID、checkpoint、loss、吞吐或显存结果 |
| 下游评测 | UNKNOWN | NOT STARTED | 无预测、seed、统计检验或结果图表 |
| 论文性能主张 | UNKNOWN | NOT STARTED | 当前不允许声称超过任何模型 |

## 2. 已完成的从零重置

### 2.1 本地清理

在确认项目根目录不是符号链接、不是挂载点、没有BrassicaceaeGenomeFM的SLURM作业或训练进程后，删除了项目中的旧内容，包括：

- B/C1/C2/D全部旧token shard；
- `training_server_transfer`旧bundle；
- 旧annotation、sampling、sequence索引；
- 旧candidate、manifest、summary、配置和SLURM脚本；
- 旧README、交接、计划、模型结构、目录结构和进展文档。

**2026-08-02 14:47:59 CST（UTC+08:00）** 复核时，项目根目录除`.git`外为空，外部原始数据目录仍存在。

### 2.2 删除边界

已删除的是 `/home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel` 内的历史项目产物。以下内容没有被删除：

- 项目外部原始植物数据库；
- 其他项目文件；
- 其他项目SLURM作业；
- 其他项目cron/监控；
- 凭据、密钥和用户环境。

## 3. 新原始池的当前事实

重新进行的只读顶层扫描显示，外部广义植物池当前有：

- 1,983个顶层assembly目录；
- 1,966个候选genome文件；
- 575个候选annotation文件。

这些数字不是十字花科语料数量。当前新项目有效assembly数仍为 **N/A（尚未接受任何新release成员）**，因为以下步骤均未执行：

- NCBI Taxonomy和物种名统一；
- Brassicaceae家族筛选；
- 来源、版本、许可元数据和checksum冻结；
- assembly/contig QC；
- 精确重复和近重复聚类；
- 注释质量分层。

后续报告不得恢复旧项目的66个assembly、54B shard或其他历史数字作为新项目进展。

## 4. 文献调研完成情况

### 4.1 Nature Portfolio核心范围

已经系统核验并用于设计的核心家族包括：

- DeepSEA、ExPecto、Akita、BPNet、Enformer、Sei、Orca、DeepSTARR；
- GROVER、AgroNT、PlantCAD2、Nucleotide Transformer、Borzoi；
- Evo、GPN-MSA、GET；
- DNA foundation model benchmark、SegmentNT、DNALONGBENCH、OmniReg-GPT；
- AlphaGenome、Evo 2、UKBioBERT/UKBioFormer、Corgi、SUCCEED。

关键正式来源及其设计作用已写入 `TRAINING_PLAN.md`。检索中剔除了蛋白模型、纯转录组模型、量子算法GROVER同名结果和与DNA表征无直接关系的普通基因组文章。

### 4.2 植物和外部模型

已经纳入必须公平比较的模型：

- AgroNT和Plants Genomic Benchmark；
- PlantCAD2-M/L及其12项zero-shot、7项微调范式；
- PlantCaduceus；
- GPN Arabidopsis/Brassicales；
- DNABERT、DNABERT-2/GUE；
- Nucleotide Transformer；
- HyenaDNA、Caduceus；
- GPN-MSA、Evo/Evo 2；
- AlphaGenome、Enformer、Borzoi等任务专家。

这些模型目前只是冻结的baseline清单，尚未下载、安装或重跑。论文公开分数不会被复制成本项目结果。

## 5. 已冻结的最终科学设计

### 5.1 数据

- 一个逻辑数据release，而不是B/C1/C2/D四套数据；
- 下游task registry和clean-inductive/label-transfer身份在预训练release前冻结；
- contig只编码一次，窗口由唯一catalog索引；
- exact、reverse-complement exact、区间重叠和ANI近重复四层控制；
- similarity-cluster-aware split；
- 属、assembly、近重复簇、region和context联合平衡；
- 4K/8K/16K/32K/64K/128K混合；
- 每个coverage cycle内部同一anchor无放回；首轮优先覆盖未见anchor，跨cycle按冻结暴露规则受控复用；
- 正式run不设置累计token或optimizer-step上限，由冻结development收敛/过拟合条件触发WSD衰减并停止；
- 长期4K/8K/16K/32K/64K/128K token比例固定为9.5%/19.0%/19.5%/25.0%/21.0%/6.0%；10,000-step表只作记账示例，不是训练阶段或上限；
- 固定development panel为3,492窗口/50,331,648 tokens；sealed pretraining test为6,948窗口/100,663,296 tokens；acceptance pool为4,320窗口/117,964,800 tokens；
- `unique_corpus_tokens_covered`、`scheduled_sampling_tokens`、`processed_forward_tokens`和各类`valid_objective_targets`分开记账；
- sequence和逐碱基结构标签存入同一自包含release。

### 5.2 模型

- 名称：`BrassiCaduceus-330M`；
- 47层、`d_model=1024`、双向tied-projection Mamba；
- 骨干330,985,472参数；
- 含正式预训练head的训练图331,661,083参数；
- 单碱基、最大128K；
- MLM + region + frame + boundary + RC consistency + homeolog contrastive；
- Caduceus-PH式RC conjoining，不声称严格结构等变。

### 5.3 训练

- 3张A100 40GB、3进程DDP；
- bf16、FP32 residual、hierarchical/selective checkpoint、fused selective scan；
- 每GPU每micro-step目标131,072 tokens；
- 三卡、梯度累积2后每optimizer step固定调度786,432个scheduled sampling tokens；
- 单一连续run，从第一步起由累计token缺口调度器维持固定长期长度比例；
- WSD学习率：1,000步warmup，stable段无预定结束step；首轮coverage完成且至少20,000步后，冻结development停滞/过拟合条件可触发10,000步cosine decay并停止；
- 不允许用缩小模型替代128K正式硬件验收；完整模型必须连续100个128K optimizer steps并在第50步跨进程恢复，4K/8K/16K/32K/64K另各10 steps。

### 5.4 下游

公共任务覆盖调控分类、植物PGB、PlantCAD2兼容任务、单碱基结构、表达、长程调控、3D和变异效应。专属任务覆盖：

- U三角亚基因组与homeolog检索；
- 多倍体表达偏倚；
- 全基因组三倍化后的保留/分馏；
- homeologous exchange/gene conversion；
- S-locus自交不亲和；
- 春化和开花；
- 硫代葡萄糖苷和油用品质；
- NLR/clubroot/blackleg抗病；
- PAV/SV/TE；
- 驯化、改良和生态适应；
- 基因簇长程协同；
- 跨属低样本迁移。

完整输入、标签、split、hard negative、指标、基线和证据边界见 `DOWNSTREAM_TASKS.md`。

## 6. 下一次执行的唯一顺序

当前第一优先级不是提交GPU训练，而是建立可信的新数据release：

1. 冻结下游task registry、primary endpoint、独立单位和预训练排除hash；
2. 从广义植物池重新解析taxonomy和来源；
3. 冻结十字花科候选assembly；
4. 运行assembly/contig QC、exact/near-duplicate及orthogroup/LD/haplotype聚类；
5. 冻结exposure-aware cluster split；
6. 构建sequence、annotation、TE、structure和homeolog标签；
7. 生成唯一window catalog、overlap anchor、context容量/混杂审计，以及各pool的coverage-cycle排列、复用上限和deficit规则；
8. 生成全checksum、自包含bundle并离线验证；
9. 实现完整330M模型、全局有效目标归一化和训练代码；
10. 使用完整模型完成三卡100-step 128K语义/硬件验收；
11. 启动一条无预定总token/step上限的连续run，只用冻结development规则触发WSD decay并选择winner；
12. 冻结winner后执行五seed下游和一次sealed test。

这不是多个模型版本，而是同一个最终设计必须依次通过的数据、实现、硬件和科学证据Gate。

## 7. 结果栏

| 结果 | 当前值 |
|---|---|
| 新有效Brassicaceae assemblies | N/A |
| 去重后train tokens | N/A |
| 累计scheduled / processed tokens | N/A |
| 首轮unique coverage / exposure-equivalent | N/A |
| 128K可训练性 | N/A |
| 实测tokens/s | N/A |
| 峰值显存 | N/A |
| 最终checkpoint | N/A |
| development loss | N/A |
| sealed test loss | N/A |
| 通用下游结果 | N/A |
| 十字花科专属结果 | N/A |
| 相对最强公共模型提升 | N/A |

只有真实机器产物出现后才更新此表，禁止填入计划值、模拟值或论文中的外部结果。

## 8. 精确进展日志

- **2026-08-02 14:47:59 CST（UTC+08:00）**：复核项目旧内容已清空，根目录只保留`.git`；外部原始植物数据库保持存在。
- **2026-08-02 14:57:01 CST（UTC+08:00）**：完成训练方案、330M架构、训练进展和下游任务四份新文档初稿，未生成任何额外项目文件。
- **2026-08-02 15:10:35 CST（UTC+08:00）**：完成四文件allowlist、Markdown表格、参数量与token算术、敏感信息和链接检查；44个唯一外部链接均直接可访问或由Crossref精确DOI回退核验，Europe PMC可匹配的40条文献没有撤稿/撤回标记，另两条由Crossref与OpenAlex确认题名且`is_retracted=false`。
- **2026-08-02 15:48:17 CST（UTC+08:00）**：完成第二轮漏洞审计的主要修补。修补了下游test身份晚于预训练冻结、公共模型暴露不对称、mixed-length/DDP按窗口错误归一化、unique与processed token混淆、RC额外计算漏报、IUPAC信息丢失、annotation-rich assembly梯度支配、逐block checkpoint在128K的显存风险、单步128K门禁过弱、checkpoint选择指标不明确和永久checkpoint过量等问题。
- **2026-08-02 16:04:37 CST（UTC+08:00）**：审计冻结。进一步补齐clean-inductive 131,071 bp禁入halo、pretraining-seed主张边界、语料因果归因边界、十个确认性家族/11个primary hypotheses的统一Holm规则和pair anchor不复用合同；四文件allowlist、Markdown表格、参数/54B step/混长积分比例/显存算术、敏感信息与44个链接再次通过验证（41个直接访问、3个Crossref精确回退）。此处54B是当时方案，已于2026-08-03被无预定上限的WSD合同取代；科学执行状态仍为NOT STARTED。
- **2026-08-02 18:03:50 CST（UTC+08:00）**：完成AgroNT、PlantCAD2、PlantCaduceus、GPN、NT-v2-500M和Evo 2的论文/模型卡/公开权重核验，新增自包含综合Markdown和正式Word；当时冻结68,664-step窗口表、development/sealed test/acceptance精确panel和20项下游任务。该固定step表已于2026-08-03改为无上限长期比例记账；其余panel和任务体系继续有效。科学执行状态仍为NOT STARTED。
- **2026-08-03 08:27:28 CST（UTC+08:00）**：按用户决策取消正式预训练的预定总token/optimizer-step上限。训练改为coverage cycle内无放回、跨cycle受控复用，四类token分账，固定长期context比例和10,000步参考记账；首轮coverage完成且至少20,000步后，按冻结development停滞/过拟合条件触发10,000步WSD decay。补齐exposure里程碑和compute-matched checkpoint合同，并同步训练、架构、下游、综合说明和Word。Word经LibreOffice 7.6真实转PDF为30页，目录实页码、4个横向宽表、中文字体和全部页面视觉检查通过，无空白/稀疏页；六文件allowlist、Markdown表格、参数/10,000步/panel算术、旧合同残留、DOCX ZIP/正文、PDF页面、敏感信息和53个外部链接全部通过。科学执行状态仍为NOT STARTED。

Git commit和远端SHA不能写入产生该SHA的同一文件中，最终远端发布状态以Git/GitHub回读receipt和本次交付回复为准，不将仓库操作混作训练科学结果。

## 9. 唯一文档集合

新项目只保留以下六份轻量文档：

1. `TRAINING_PLAN.md`：最终训练方案与文献依据；
2. `MODEL_ARCHITECTURE.md`：最终330M架构；
3. `TRAINING_PROGRESS.md`：真实执行状态；
4. `DOWNSTREAM_TASKS.md`：通用和十字花科专属评测体系；
5. `BRASSICACEAE_GENOMEFM_COMPREHENSIVE_DESIGN.md`：自包含的最详细研究设计说明；
6. `BRASSICACEAE_GENOMEFM_COMPREHENSIVE_DESIGN.docx`：与第五项内容一致的正式Word版。

旧README、旧handoff、旧计划和其他历史说明不再恢复。Git提交只允许这六份轻量文档；原始数据、shard、candidate、label、日志、checkpoint和大型结果不得上传GitHub。
