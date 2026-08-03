# BrassicaceaeGenomeFM 最终训练方案

## 0. 文档性质与证据边界

这是从零重建后的唯一训练方案，面向正式论文与正式训练，不是测试版、缩小版或过渡方案。

- 目标模型：`BrassiCaduceus-330M`，约 3.31 亿参数，单碱基、双向、Mamba/Caduceus 风格。
- 目标硬件：3 张 NVIDIA A100 40 GB。
- 训练形态：4K、8K、16K、32K、64K、128K 六种上下文混合在同一条连续训练中；不重置模型、优化器或学习率计划。
- 训练抽样：每个coverage cycle内部严格无放回，跨cycle按冻结暴露规则受控复用；不采用普通独立有放回随机抽样。
- 数据范围：只以重新核验的十字花科核基因组为预训练主体；近缘目外数据不混入主体预训练。
- 当前事实：旧数据、旧 shard、旧配置和旧计划已经删除；新语料、新模型代码和新训练尚未执行。本文写的是冻结的执行合同，不把设计写成结果。

预期论文主张必须同时由三类证据支持：

1. 在通用 DNA/植物基因组任务上达到与公开强模型可比或更好；
2. 在严格防泄漏的十字花科专属任务上稳定超过公共通用模型、植物模型和同架构随机初始化；
3. 证明优势不是来自随机划分、数据重复或更大的下游head，并用消融检验超长上下文、结构监督和homeolog目标；若没有再训练一个同架构、同token、同QC的广义植物语料控制模型，只能说“十字花科专属系统整体优于公共通用模型”，不能把增益因果归于十字花科语料本身。

在正式结果产生前，禁止使用“已完成多任务预训练”“已超过基线”“已支持128K训练”等措辞。

## 1. 文献调研范围与设计依据

### 1.1 检索范围

文献检索冻结到 2026-08-02，检索源包括 Nature Portfolio、Crossref、PubMed/Europe PMC、论文正式页面以及公开模型仓库。查询族覆盖：

- DNA/genome foundation model、DNA/genomic language model、nucleotide transformer；
- sequence-to-function、gene-expression prediction、variant-effect prediction；
- single-nucleotide genome annotation、long-range DNA、3D genome；
- plant/crop genomic foundation model；
- AlphaGenome、Evo/Evo 2、Nucleotide Transformer、AgroNT、GROVER、SegmentNT、Enformer、Borzoi、GPN-MSA 等模型名。

纳入的是与本项目输入和任务直接相关的原始研究、正式 benchmark 和关键方法论文。仅使用转录组输入的单细胞模型、蛋白质语言模型、量子算法中同名的 GROVER，以及不提供可迁移 DNA 表征的普通任务模型不进入核心证据集。因此，“全部”指本项目技术边界内检索到的直接相关模型家族，不是把所有标题中出现 genome 的论文机械罗列。

### 1.2 Nature Portfolio 核心证据

| 主题 | 论文与正式链接 | 本项目吸收的证据 | 不直接照搬之处 |
|---|---|---|---|
| 非编码变异 | DeepSEA, Nature Methods 2015, [10.1038/nmeth.3547](https://doi.org/10.1038/nmeth.3547) | 从 DNA 直接预测染色质状态并进行单碱基变异评分 | 人类任务特异，短上下文 |
| 表达与疾病变异 | ExPecto, Nature Genetics 2018, [10.1038/s41588-018-0160-6](https://doi.org/10.1038/s41588-018-0160-6) | 组织特异表达和饱和突变评估 | 依赖人类表观组输出 |
| 3D基因组 | Akita, Nature Methods 2020, [10.1038/s41592-020-0958-x](https://doi.org/10.1038/s41592-020-0958-x) | 长区间和结构变异的序列效应 | 任务专用 CNN，不是通用预训练模型 |
| 碱基级调控语法 | BPNet, Nature Genetics 2021, [10.1038/s41588-021-00782-6](https://doi.org/10.1038/s41588-021-00782-6) | 碱基级 profile、motif syntax 和匹配负例 | 需要高质量实验 track |
| 长程表达 | Enformer, Nature Methods 2021, [10.1038/s41592-021-01252-x](https://doi.org/10.1038/s41592-021-01252-x) | 约200 kb输入、长程调控和表达/变异任务 | 人鼠监督训练，不能作为纯自监督等价基线 |
| 全局调控图谱 | Sei, Nature Genetics 2022, [10.1038/s41588-022-01102-2](https://doi.org/10.1038/s41588-022-01102-2) | 多任务调控表征和 sequence class | 监督 track 数量远超当前植物数据 |
| 多尺度3D结构 | Orca, Nature Genetics 2022, [10.1038/s41588-022-01065-4](https://doi.org/10.1038/s41588-022-01065-4) | 从 kb 到染色体尺度的结构任务设计 | 不适合作为统一预训练骨干 |
| 增强子设计 | DeepSTARR, Nature Genetics 2022, [10.1038/s41588-022-01048-5](https://doi.org/10.1038/s41588-022-01048-5) | 定量 enhancer activity 与实验验证范式 | 生成设计不作为本项目首篇主张 |
| 人类DNA语言 | GROVER, Nature Machine Intelligence 2024, [10.1038/s42256-024-00872-0](https://doi.org/10.1038/s42256-024-00872-0) | BPE 与基因组上下文表征的系统分析 | 可变 token 会削弱单碱基定位，不采用 |
| 植物基础模型 | AgroNT, Communications Biology 2024, [10.1038/s42003-024-06465-2](https://doi.org/10.1038/s42003-024-06465-2) | 48种植物、PGB、调控注释、启止子强度、表达和变异任务 | 1B Transformer 不是3×40GB下的最佳长序列骨干 |
| 被子植物长上下文模型 | PlantCAD2, bioRxiv 2025, [10.1101/2025.08.27.672609](https://doi.org/10.1101/2025.08.27.672609) | 65种被子植物、单碱基Mamba2、8,192 bp、12项zero-shot和7项微调范式 | 仍是预印本；约311M的M版是规模匹配关键基线，约694M的L版是强植物上界；8K和gene-centered语料不覆盖本项目全部128K专属问题 |
| 多物种Transformer | Nucleotide Transformer, Nature Methods 2024/2025, [10.1038/s41592-024-02523-z](https://doi.org/10.1038/s41592-024-02523-z) | 50M–2.5B规模、低数据迁移和多任务评估 | 主要是短上下文 Transformer |
| RNA覆盖 | Borzoi, Nature Genetics 2025, [10.1038/s41588-024-02053-6](https://doi.org/10.1038/s41588-024-02053-6) | 从序列统一预测转录、剪接和加尾 | 数据和输出主要为人类/小鼠 |
| 原核长序列FM | Evo, Nature Genetics 2025, [10.1038/s41588-024-02062-5](https://doi.org/10.1038/s41588-024-02062-5) | 单碱基长序列状态空间建模 | 原核语料与植物染色体结构差异大 |
| 比对增强变异模型 | GPN-MSA, Nature Biotechnology 2025, [10.1038/s41587-024-02511-w](https://doi.org/10.1038/s41587-024-02511-w) | 多物种比对支持的全基因组变异效应 | MSA 是额外输入，必须单列比较 |
| 转录基础模型 | GET, Nature 2025, [10.1038/s41586-024-08391-z](https://doi.org/10.1038/s41586-024-08391-z) | 跨细胞类型转录调控与远端元件 | 输入含染色质可及性，不属于 DNA-only 主榜 |
| 公平评测 | Benchmarking DNA foundation models, Nature Communications 2025, [10.1038/s41467-025-65823-8](https://doi.org/10.1038/s41467-025-65823-8) | 同一任务重跑、pooling敏感性、通用模型并非所有任务都占优 | 不复制论文表中分数，必须在本项目 split 上真实重跑 |
| 单碱基分割 | SegmentNT, Nature Methods 2025, [10.1038/s41592-025-02881-2](https://doi.org/10.1038/s41592-025-02881-2) | 14类多标签语义分割、50 kb NT 与最长500 kb集成 | 本项目必须改为植物重叠转录本和十字花科标签体系 |
| 超长基准 | DNALONGBENCH, Nature Communications 2025, [10.1038/s41467-025-65077-4](https://doi.org/10.1038/s41467-025-65077-4) | 五类最长1 Mb长程任务及专家模型对照 | 人类任务不能直接证明植物专属价值 |
| 全尺度生成FM | OmniReg-GPT, Nature Communications 2025, [10.1038/s41467-025-65066-7](https://doi.org/10.1038/s41467-025-65066-7) | 从局部元件到3D接触的统一尺度设计 | 生成能力不作为当前主模型必需条件 |
| 统一序列到功能 | AlphaGenome, Nature 2026, [10.1038/s41586-025-10014-0](https://doi.org/10.1038/s41586-025-10014-0) | 1 Mb输入、单碱基输出、多模态和25/26变异评测范式 | 人鼠监督模型；植物数据不支持原样复制数千 tracks |
| 跨生命域生成 | Evo 2, Nature 2026, [10.1038/s41586-026-10176-5](https://doi.org/10.1038/s41586-026-10176-5) | 9万亿碱基、1M上下文、预测与设计并重 | 规模和硬件远超本项目，且专属十字花科深度不足 |
| 变异参与预训练 | UKBioBERT/UKBioFormer, npj Artificial Intelligence 2026, [10.1038/s44387-026-00103-4](https://doi.org/10.1038/s44387-026-00103-4) | 变异感知表征与 sequence-to-function 融合 | 不能把人群变异标签泄漏进十字花科 sealed test |
| 条件化功能预测 | Corgi, Nature Communications 2026, [10.1038/s41467-026-75527-2](https://doi.org/10.1038/s41467-026-75527-2) | DNA与转因子环境分开建模，支持未见条件 | 多组学条件输入必须放扩展榜，不与 DNA-only 主榜混合 |
| 监督基础模型 | SUCCEED, Nature Communications 2026, [10.1038/s41467-026-73129-6](https://doi.org/10.1038/s41467-026-73129-6) | 6,389条功能组学 tracks 的监督预训练价值 | 当前植物 track 覆盖不足，不能伪造同等监督规模 |

为避免只列“著名模型”造成检索遗漏，下列 Nature Portfolio 论文也已完成题名/DOI筛查。它们主要作为任务、工具或边界证据，而不是与本项目同构的主骨干：

| 类型 | 论文与正式链接 | 在本项目中的位置 |
|---|---|---|
| 基因组到蛋白功能 | *Genomic language model predicts protein co-regulation and function*, Nature Communications 2024, [10.1038/s41467-024-46947-9](https://doi.org/10.1038/s41467-024-46947-9) | 作为跨层级功能任务参考，不与DNA-only碱基任务混榜 |
| 系统发育更新 | *PhyloTune*, Nature Communications 2025, [10.1038/s41467-025-61684-3](https://doi.org/10.1038/s41467-025-61684-3) | 作为embedding与系统发育迁移扩展任务 |
| 单细胞序列到功能 | *scooby*, Nature Methods 2025, [10.1038/s41592-025-02854-5](https://doi.org/10.1038/s41592-025-02854-5) | 多模态单细胞扩展榜，不进入DNA-only主榜 |
| 建模与设计框架 | *gReLU*, Nature Methods 2025, [10.1038/s41592-025-02868-z](https://doi.org/10.1038/s41592-025-02868-z) | 作为下游实现与序列设计工具参考 |
| 基因设计 | *Semantic design of functional de novo genes from a genomic language model*, Nature 2025/2026, [10.1038/s41586-025-09749-7](https://doi.org/10.1038/s41586-025-09749-7) | 说明生成式验证标准；首篇不把生成作为主张 |
| DNA-FM评论/基准解读 | *Benchmarking genomic language models*, Nature Methods 2025, [10.1038/s41592-025-02829-6](https://doi.org/10.1038/s41592-025-02829-6) | 支持统一pooling、任务专用模型和FM分层比较 |
| 3D基础模型 | *A foundation model to help understand the regulatory implications of 3D genome organization*, Nature Methods 2026, [10.1038/s41592-026-03098-7](https://doi.org/10.1038/s41592-026-03098-7) | Hi-C输入扩展榜；不能冒充DNA-only任务 |
| 跨染色体结构 | *Prediction and functional interpretation of inter-chromosomal genome architecture from DNA sequence with TwinC*, Nature Communications 2026, [10.1038/s41467-026-72031-5](https://doi.org/10.1038/s41467-026-72031-5) | 3D结构任务和跨染色体边界参考 |
| ab initio注释 | *Highly accurate ab initio gene annotation with ANNEVO*, Nature Methods 2026, [10.1038/s41592-026-03036-7](https://doi.org/10.1038/s41592-026-03036-7) | 单碱基注释专家基线候选 |
| promoter语言模型 | *Decoding promoter activity from DNA sequence using pre-trained language models*, Scientific Reports 2026, [10.1038/s41598-026-61483-w](https://doi.org/10.1038/s41598-026-61483-w) | promoter任务应用证据，不单独定义基础模型家族 |
| 综述 | *Predicting gene expression from DNA sequence using deep learning models*, Nature Reviews Genetics 2025, [10.1038/s41576-025-00841-2](https://doi.org/10.1038/s41576-025-00841-2) | sequence-to-expression范围、局限和评测背景 |
| 综述 | *The DNA dialect: a comprehensive guide to pretrained genomic language models*, 2026, [10.1038/s44320-025-00184-4](https://doi.org/10.1038/s44320-025-00184-4) | 检索补充与术语统一，不替代原始论文证据 |

另筛到的 nanopore chimera校正、抗生素抗性识别和罕见人类编码变异应用论文只证明DNA语言模型可被任务化，不改变本项目架构或核心榜，因此不扩展成新的模型家族。

### 1.3 必须纳入的外部非 Nature 基线

- DNABERT: Bioinformatics 2021, [10.1093/bioinformatics/btab083](https://doi.org/10.1093/bioinformatics/btab083)。
- DNABERT-2/GUE: [arXiv:2306.15006](https://arxiv.org/abs/2306.15006)，公开117M检查点与28项GUE任务。
- HyenaDNA: NeurIPS 2023, [10.52202/075280-1872](https://doi.org/10.52202/075280-1872)，单碱基、最长1M上下文。
- Caduceus: ICML 2024, [PMLR 235:5044-5081](https://proceedings.mlr.press/v235/schiff24a.html)，双向与反向互补建模，公开131K检查点。
- GPN: PNAS 2023, [10.1073/pnas.2311219120](https://doi.org/10.1073/pnas.2311219120)，在 Arabidopsis 及近缘 Brassicales 上做零样本变异效应。
- PlantCaduceus: PNAS 2025, [10.1073/pnas.2421738122](https://doi.org/10.1073/pnas.2421738122)，16种被子植物、单碱基跨物种迁移。
- PlantCAD2: bioRxiv 2025, [10.1101/2025.08.27.672609](https://doi.org/10.1101/2025.08.27.672609)，65种被子植物、Mamba2、8,192 bp；正式比较同时锁定约311M的M版和约694M的L版公开revision，并以运行时参数receipt处理摘要“676M”与正文“694M”的数字差异。
- Genomic Benchmarks: BMC Genomic Data 2023, [10.1186/s12863-023-01123-8](https://doi.org/10.1186/s12863-023-01123-8)。

## 2. 新数据语料的定义

### 2.1 当前原始来源事实

2026-08-02 的重新扫描只确认外部只读目录 `/home/user/zhangzhishuai/data/plantDB/genome` 中存在：

- 1,983 个顶层 assembly 目录；
- 1,966 个候选 genome 文件；
- 575 个候选 annotation 文件。

这是广义植物原始池，不等于十字花科有效语料。当前新项目接受的 assembly 数为0；必须重新做分类学、来源、质量、重复和注释审计，禁止恢复旧 manifest 的数字。

### 2.2 纳入规则

每个 assembly 必须具备稳定来源ID、物种名、NCBI Taxonomy ID、下载来源、版本、文件 SHA-256 和抓取日期。主体语料只纳入 NCBI Taxonomy 明确属于 Brassicaceae 的核基因组。

优先级：

1. 染色体级、参考级或高连续性组装；
2. 能映射到明确 accession/品种/生态型；
3. 同一生物材料多版本时保留质量最优、注释最完整者；
4. 单倍型、泛基因组和不同品种可保留，但必须进入近重复簇并限制权重；
5. 叶绿体、线粒体、质粒、病原污染和未定位小污染 contig 不进入核基因组主训练；可单列到未来分析，不混入主语料。

### 2.3 Assembly QC

每个 assembly 生成不可变 QC receipt，至少包含：总长度、contig/scaffold 数、N50/L50、最大 contig、N比例、GC、非ACGTN字符、BUSCO、污染检查、物种预期大小偏差和注释可用性。

硬门禁：

- 物种和 taxonomy 冲突：拒绝；
- 非ACGTN字符未规范化：拒绝；
- 核基因组 N 比例大于5%：拒绝主体语料；
- 总长度偏离同属中位数超过4个 MAD 且无多倍体/单倍型解释：人工核验，否则拒绝；
- 明显重复发布的同一 assembly：只保留一份；
- BUSCO 和 annotation 质量只决定是否进入结构监督层，不允许用低质量注释产生“真值”。

长上下文资格按 contig 单独判断。assembly 可以进入4K/8K语料，但只有满足长度和局部QC的 contig 才进入64K/128K。

### 2.4 窗口级 QC

每个候选窗口在真实局部序列上重新计算，而不是沿用 contig 级统计：

- `N_fraction <= 1%`；
- 不允许长度大于等于32 bp的连续N；
- 非ACGTN计数必须为0；
- 检测极低复杂度和串联重复，但不机械删除真实TE、着丝粒或抗病基因簇；低复杂度状态作为分层和权重字段；
- 窗口不能跨 contig；
- 训练、验证、测试使用相同QC代码和冻结阈值。

## 3. 精确去重、近重复控制与 split

### 3.1 三层去重

1. **Assembly/contig精确去重**：解析FASTA后转大写、规范字符，计算真实序列 hash；不能用 gzip 文件 hash 代替序列身份。
2. **窗口精确去重**：对 `sequence` 与 `reverse_complement(sequence)` 取 canonical hash；正向和反向互补完全相同的窗口只保留一条。
3. **区间重叠去重**：同一 contig 上相互覆盖超过80%的候选窗口归入同一 `anchor_id`；正式训练只从同一 anchor 选择一种上下文长度。

### 3.2 近重复聚类

- 用 Mash/sourmash MinHash 做候选搜索，再用 ANI/局部比对确认；不能只凭 sketch 阈值删除。
- ANI不低于99.9%、对齐覆盖不低于90%的 assembly 默认视为实质重复；保留质量最优代表。若是有明确生物意义的不同单倍型，可保留，但同簇同split且限额。
- ANI 99.5%–99.9%的 assembly 放入同一 similarity cluster，不跨 split。
- 窗口跨 split 若 identity 不低于98%且覆盖较短窗口不低于80%，必须合并到同簇或从评估集移除。
- 普通同源基因、远缘保守元件和多倍体 homeolog 不应在 train 内被一刀切删除；对它们采用“同簇、限额、分层”，保留生物进化信号。

### 3.3 Split合同

split 在任何模型训练、标签统计或超参数选择前冻结：

- train：目标约90%的合格callable token容量；
- development：目标约5%的合格callable token容量，只用于损失监控、checkpoint选择和训练期调参；
- sealed test：目标约5%的合格callable token容量，正式 winner 与seed矩阵冻结后只读取一次；
- 额外保留未参加预训练的 Brassicales 外群和未见属，作为迁移评估，不混入 sealed family test。

相似性簇是不可拆分原子，90/5/5是token容量目标而不是简单按簇数量切片。使用确定性约束求解同时平衡属、物种、倍性、assembly质量、注释覆盖和六个context容量；报告目标与实际的cluster数、assembly数和token数。若巨大簇或小属使比例不可同时满足，优先保证无泄漏与“整属留出”，如实报告偏差，不能拆簇硬凑90/5/5。

任何下游任务都建立独立 split；预训练 split 不能替代 orthogroup、品种、群体、研究批次或染色体级防泄漏。

### 3.4 下游评测防火墙必须先于预训练release

只先冻结预训练split、以后再设计下游任务，会让目标test序列悄悄进入预训练。正式顺序必须改为：先冻结下游task registry和独立单位，再冻结预训练可消费集合。每项任务写入一张 `pretraining_exposure_matrix`，至少记录 exact assembly、同物种、同属、同科、exact/RC-exact窗口、近重复窗口、orthogroup、LD block、haplotype clan 和 study 是否出现在预训练train。

任务分为三条不能混写的证据轨道：

1. **clean-inductive**：sealed test的assembly/区域/orthogroup/haplotype及其近重复组件全部从预训练train、development、acceptance pool和所有辅助标签中排除；区域级holdout还要向两侧扩展`max_context-1 = 131,071 bp`作为禁入halo，任何预训练窗口只要与halo相交就拒绝，防止128K窗口从外围包含test区域。只有这条轨道可支持“预训练和checkpoint选择均未见”。
2. **label-transfer**：允许目标无标签DNA进入MLM，但目标任务标签、配对和统计量完全隔离；只能称“标签迁移”，不能称序列未见。
3. **public-exposure-unknown**：公共模型无法完整追溯预训练暴露时，保留比较但显式标记，不能把暴露不对称解释为纯架构胜负。

下游sealed identity清单只保存哈希和独立单位ID供语料构建器执行排除，训练代码无权读取标签。预训练release必须绑定task-registry hash和exposure-matrix hash；任一任务身份变化都会使原release不再支持该任务的clean-inductive主张。

## 4. 一个逻辑数据集，而不是四套 shard

### 4.1 存储结构

新语料只建立一个逻辑 release，物理上可分片以支持并行I/O：

- `sequence_store`：每条合格contig的canonical ACGTN视图只编码一次，uint8/mmap随机访问；IUPAC原字符以稀疏`ambiguity_sidecar`保留，不复制整条序列；
- `contig_index`：assembly、contig、全局offset、长度、taxonomy和checksum；
- `window_catalog`：唯一窗口ID、anchor、坐标、context长度、region、QC、split、相似性簇；
- `label_store`：每条 contig 的结构标签和有效性 mask 只保存一次；
- `pair_catalog`：高置信 syntenic ortholog/homeolog 配对；
- `provenance`：来源、许可元数据、软件版本、命令摘要和所有SHA-256。

“一个数据集”不等于一个巨型文件。使用多个内容寻址 shard，但只能有一份 catalog、一份split和一个 release ID。

### 4.2 编码合同

原始 sequence store：`A=0, C=1, G=2, T=3, N=4`。

模型词表：`PAD=0, A=1, C=2, G=3, T=4, N=5, MASK=6, RESERVED=7`。

DataLoader 必须显式执行 `model_id = raw_id + 1`；PAD只能来自实际补齐，不能把 raw `A=0` 当PAD。每次发布必须用全量值域统计和已知序列 fixture 验证 remap、reverse complement 与mask。

原始FASTA中的标准IUPAC歧义字符 `RYSWKMBDHV` 不可被无痕删除：source view原样保留，canonical model view才映射为N；其他非法符号fail-closed。每条contig同时保存 `source_sequence_sha256` 与 `canonical_acgtn_sha256`，发布后从随机访问store回读并重建两个hash，不能只相信writer写出时计算的hash。

## 5. 多长度、coverage-cycle受控复用的正式采样

### 5.1 上下文集合与长期比例

固定上下文为：4,096、8,192、16,384、32,768、65,536、131,072 bp。所有长度从第一步到停止都属于同一条连续训练run；不因进入新coverage cycle、WSD衰减或作业续跑而重置模型、优化器或全局step。

长期目标比例按`scheduled_sampling_tokens`定义，而不是按窗口条数定义：

| 长度 | 长期token比例 | 全局窗口/optimizer step |
|---:|---:|---:|
| 4K | 9.5% | 192 |
| 8K | 19.0% | 96 |
| 16K | 19.5% | 48 |
| 32K | 25.0% | 24 |
| 64K | 21.0% | 12 |
| 128K | 6.0% | 6 |

训练不再使用依赖预定终点的`u=t/T`长度课程。bucket调度器从第一步起按确定性“累计目标token缺口最大者优先”选择长度；三个DDP rank在同一micro-step使用相同长度。中断和恢复后从累计缺口状态继续，不重新开始比例统计。

为便于核验，以下10,000-step记账块只说明长期比例如何落实，不是训练上限、阶段长度或停止点：

| context | 长期token比例 | 全局窗口/step | 每10,000步参考steps | 参考窗口数 | 参考scheduled tokens |
|---:|---:|---:|---:|---:|---:|
| 4,096 | 9.5% | 192 | 950 | 182,400 | 747,110,400 |
| 8,192 | 19.0% | 96 | 1,900 | 182,400 | 1,494,220,800 |
| 16,384 | 19.5% | 48 | 1,950 | 93,600 | 1,533,542,400 |
| 32,768 | 25.0% | 24 | 2,500 | 60,000 | 1,966,080,000 |
| 65,536 | 21.0% | 12 | 2,100 | 25,200 | 1,651,507,200 |
| 131,072 | 6.0% | 6 | 600 | 3,600 | 471,859,200 |
| **合计** | **100%** | — | **10,000** | **547,200** | **7,864,320,000** |

比例冻结前必须为每个bucket分别报告：合法anchor数、首轮token容量、属/物种/material/assembly覆盖、注释覆盖、N/低复杂度分布、实测tokens/s和预计墙钟时间。短context还要包含与64K/128K同源assembly质量匹配的子集，防止模型把“context长度”与碎片化assembly、特定属或注释质量混为一谈。运行中不能依据development/test表现改变长期比例；若某个pool容量不足，按5.2的deficit规则记录并机械再分配，不能让小pool无限重启来伪造比例。

### 5.2 coverage cycle与跨cycle受控复用

- 正式预训练不设置预定的累计token或optimizer-step上限。
- 每个anchor在catalog中冻结唯一context和唯一主采样channel，避免同一中心区域同时以4K和128K重复计权。
- 每个`(context, region, genus, assembly/source)` pool内部构成一个coverage cycle；cycle内采用确定性无放回排列，同一`anchor_id`最多出现一次。
- 首轮必须优先覆盖从未使用的anchor。某pool只有在本cycle耗尽后才能进入下一cycle；任何pool不得领先同context其他强制pool超过一个cycle，容量不足则记录deficit并按预先冻结的优先级再分配。
- 跨cycle允许同一anchor再次出现，但必须使用新的动态MLM mask，并可使用冻结范围内的窗口jitter或RC方向变化；这些变化不把重复来源坐标重新记成unique数据。
- DDP三个rank在同一step接收互不重叠的anchor；checkpoint保存每个pool的cycle编号、permutation hash、cursor、RNG状态和累计暴露，恢复后不得回退或重新开始cycle。
- anchor不重复仍不等于碱基绝不重叠。catalog必须报告逐assembly的source-coordinate coverage multiplicity；候选构建阶段任何碱基因不同anchor覆盖超过3次时，按确定性优先级移除多余anchor并公开分布。
- 不使用普通独立有放回weighted sampler，也不把动态训练称为完成了若干严格epoch；只报告coverage cycle、exposure-equivalent和真实累计暴露。

训练receipt同时记录四个不同分母：

- `unique_corpus_tokens_covered`：每个anchor首次被正式调度时对应的token；达到release首轮容量后不再增长；
- `scheduled_sampling_tokens`：所有primary view累计token，包含后续coverage cycle的受控复用；每optimizer step固定增加786,432，是长度比例和WSD进度的主时钟；
- `processed_forward_tokens`：实际经过骨干的全部token，包含5% RC第二视图等额外forward；
- `valid_objective_targets`：MLM/region/frame/boundary/RC/homeolog各自有效分母。

另报告`exposure_equivalent = scheduled_sampling_tokens / first_cycle_token_capacity`、每个context/region/taxon/source的cycle restart次数、exact-repeat率和source-coordinate覆盖。这个比值只是平均暴露量，不等于每个anchor恰好被看了相同次数。

固定development panel仍为64个step-equivalents、50,331,648 tokens、3,492个窗口，各长度step数为`6/12/13/16/13/4`；一次性sealed pretraining test为128个step-equivalents、100,663,296 tokens、6,948个窗口，各长度step数为`12/24/25/32/27/8`。完整模型acceptance pool由4K/8K/16K/32K/64K各10 steps和128K连续100 steps组成，共150 steps、117,964,800 tokens、4,320个窗口。三个panel与train的anchor/近重复组件两两不相交；development和test永远不跨cycle重采样。

### 5.3 平衡与小pool保护

采样分层键为`(context, region, genus, similarity_cluster, assembly, annotation_status)`。目标比例通过pool内无放回排列、pool间累计token缺口和跨cycle暴露计数共同实现。

初始约束：

- Brassica累计scheduled tokens不超过55%；
- Arabidopsis约10%–15%；
- 其余小属合计至少20%；
- 单一assembly原则上不超过3%；
- 单一近重复簇原则上不超过1.5%；
- gene-proximal、intergenic、TE/repeat、promoter-proxy和其他结构区域均需报告实际比例；
- 小属和稀有功能pool容量不足时，只能提高未暴露anchor的优先级；不能通过连续重启小pool无限复制少数locus。

配额、rare-pool最大重复暴露和deficit再分配优先级在容量报告完成后、formal run identity生成前机械冻结，不能依据下游test表现修改。发布前还要比较六个context bucket的属、assembly质量、GC、repeat、region和annotation-status分布；任何标准化差异超过预注册阈值的字段都进入分层求解或敏感性报告。不能让128K只来自少数高质量Brassica染色体，却把结果解释为纯长上下文收益。

## 6. 结构监督标签

### 6.1 标签层级

只把有直接注释证据的位置当直接标签；启发式标签单独标记为 proxy，不与直接真值混合。

- 9个可重叠区域通道：gene、exon、intron、CDS、5'UTR、3'UTR、ncRNA、TE、experiment-supported promoter；
- CDS frame：0、1、2和ignore；
- 6个稀疏边界：splice donor、splice acceptor、start codon、stop codon、TSS、TTS；
- 冲突转录本、低可信注释、缺少callable universe的位置使用ignore mask；
- promoter若只有“基因上游2 kb”启发式定义，只能作为proxy辅助标签；不得写成实验确认的启动子。

GFF3必须与FASTA精确版本绑定：seqid一一映射、坐标不越界、strand/phase合法、CDS链长度和终止语义可验证。region通道按可信转录本并集构建；同一碱基在不同转录本中frame冲突时frame设为ignore，不能任取一个isoform。重复feature ID只在明确允许的multipart feature类型和一致Parent/strand签名下接受。

辅助损失先按有效标签归一化，再按assembly汇总并做genus-aware宏平均；单一annotation-rich assembly不能通过拥有更多碱基而支配梯度。每个genus/assembly对region、frame、boundary的有效标签贡献及ignore比例都写入训练receipt。

### 6.2 多倍体与同源配对

使用高置信共线性、orthogroup和已知亚基因组坐标建立 `pair_catalog`：

- diploid ancestor–polyploid homeolog；
- A/B/C亚基因组之间的homeolog；
- 近缘ortholog；
- 同一家族但非共线的hard negative。

所有配对随 similarity cluster 一起分split，训练对不得引用development或sealed test成员。

为同时满足pair objective和cycle内无放回，进入每个coverage cycle前在train pair graph上按证据等级、共线支持和确定性hash求edge-disjoint matching：一个anchor在当前cycle最多属于一个positive pair。pair两端使用相同context并作为一个调度单元同时预留；未入matching的anchor仍可作为普通MLM单例。catalog报告候选边、冲突边、最终matching和各属/亚基因组覆盖；同一partner只能在后续cycle重新进入，不能在当前cycle临时复用。

## 7. 正式预训练目标

总损失：

`L = L_MLM + 0.25 L_region + 0.10 L_frame + 0.10 L_boundary + 0.05 L_RC + 0.05 L_homeolog`

- `L_MLM`：所有窗口上的cross-entropy；从ACGT中选择15%目标位点，80%替换MASK、10%替换均匀随机ACGT、10%保持原样。目标预算的一半为singleton，另一半按支持集1…10、`p=0.35`的截断Geometric span填充；span不跨N/PAD/contig边界。N和PAD不作为有效预测目标。
- `L_region`：仅直接或明确分层的有效区域位置，使用9通道`BCEWithLogits`；train-only inverse-sqrt-frequency权重clip到`[1,20]`。
- `L_frame`：只在高可信且frame一致的CDS内使用4类cross-entropy，其他位置ignore。
- `L_boundary`：在callable区域内使用sigmoid focal loss，`gamma=2`，每类`alpha`由train prevalence确定并clip到`[0.05,0.95]`；负例按同染色体、相同GC和区域背景匹配。
- `L_RC`：对5%的anchor同时计算正向和反向互补视图；将最终层hidden按坐标/strand对齐并L2归一化，使用逐有效位置`1-cosine_similarity`均值。不声称模型在结构上严格RC等变。
- `L_homeolog`：对高可信共线窗口做256维对称InfoNCE，cosine temperature固定`0.07`；在三个DDP rank间做可求导all-gather，排除同orthogroup、近重复簇和关系不确定序列后构造负例。

所有分母按有效标签数归一化；没有某类标签的窗口不会产生0标签假负例。损失权重在正式训练前冻结，sealed test永不参与选择。

跨gradient-accumulation和DDP不能先把每个micro-batch各自求均值再等权反向。实现必须预取一个accumulation window，分别统计六个目标的local numerator/denominator，all-reduce全局分母，并按有效目标数加权反向；否则4K和128K会被错误地按“窗口”而不是按“token/标签”加权。RC第二视图计入`processed_forward_tokens`和墙钟开销，但不增加`scheduled_sampling_tokens`；homeolog pair两个成员都必须在当前cycle尚未消费，并各自计入scheduled tokens，仅首次暴露时增加`unique_corpus_tokens_covered`。InfoNCE不得把同一orthogroup内未确认关系的序列当普通负例。

正式run中禁止动态调loss权重。100-step acceptance gate使用train-only acceptance labels分别测六个加权目标对共享骨干的梯度范数；若任一辅助目标连续10个step超过MLM梯度范数的50%并同时触发总梯度裁剪，状态为`BLOCKED_OBJECTIVE_DOMINANCE`，只能在formal run identity生成前发布新的权重合同，不能边训练边自适应或查看development/test后改权重。

## 8. 3×A100 40GB正式训练合同

### 8.1 并行和每步token

采用3进程DDP。模型状态可以在每张40GB卡上保留完整副本；主要显存风险来自128K激活而不是3.31亿参数。

| context | 每GPU micro-batch | 每GPU每micro-step token |
|---:|---:|---:|
| 4K | 32 | 131,072 |
| 8K | 16 | 131,072 |
| 16K | 8 | 131,072 |
| 32K | 4 | 131,072 |
| 64K | 2 | 131,072 |
| 128K | 1 | 131,072 |

三个rank每个micro-step合计393,216 primary sampling tokens；gradient accumulation=2，因此每个optimizer step固定调度786,432个`scheduled_sampling_tokens`。首个coverage cycle内这些也是首次暴露token；后续cycle不再称为unique。所有rank在同一micro-step使用相同context，避免长短序列造成空等。

这是待硬件验收的目标batch，不是显存已通过的事实。按331,661,083个训练参数和约16 bytes/parameter的权重、梯度、FP32 master/Adam状态上界估算，模型训练状态约4.94 GiB；单条128K的bf16 hidden约0.25 GiB、FP32 residual约0.50 GiB。若把47层每个block边界都保存，hidden+residual边界理论量约35.25 GiB，说明“逐block checkpoint”本身并不能保证40GB可行。

正式实现采用硬件实测冻结的hierarchical/selective activation checkpoint：候选以每4–6层为一组、只保存组边界并在反向重算，同时按块计算head loss，前/反向分支不同时保留大中间张量。若仍超显存，按固定顺序尝试：优化checkpoint分组与fused kernel → chunked selective scan/head → ZeRO-1或等价optimizer-state sharding → 保持全局状态连续的sequence parallel。所有方案必须保持331M参数、128K依赖范围和786,432 scheduled sampling tokens/step合同；不得缩小模型、截断上下文或静默删除128K。

### 8.2 数值和优化器

- bf16训练；FP32 residual accumulation；TF32可用于允许的矩阵运算；
- fused Mamba selective scan、fused RMSNorm、fused AdamW；
- hierarchical/selective activation checkpoint，分组和重算策略由完整128K门禁冻结；
- AdamW：`betas=(0.9, 0.95)`、`eps=1e-8`、`weight_decay=0.1`；
- WSD（Warmup–Stable–Decay）学习率：前1,000 optimizer steps从0线性warmup到`3e-4`，随后在stable段保持`3e-4`且不预设结束step；冻结development停滞/过拟合条件触发后，执行固定10,000-step cosine decay到`3e-5`并停止；
- global gradient norm clip=1.0；
- dropout=0；随机性来自mask、RC、cycle排列和冻结范围内的窗口jitter；
- 训练seed固定，同时保存Python、NumPy、PyTorch CPU/CUDA随机状态。

正式预训练只承诺一条完整lineage；取消累计token上限不等于拥有五条独立331M基础预训练。不能用五个下游head/fine-tuning seed声称“预训练seed稳定”；预训练随机性局限必须在论文中披露，五seed只检验冻结backbone之后的下游拟合稳定性。

### 8.3 正式启动门禁

正式数据和完整330M模型完成后，必须使用一个从正式语料永久排除的acceptance pool运行真实128K硬件验收。它不是缩小模型的测试版，而是正式实现的可执行性验收：连续运行100个128K optimizer steps，在第50步原子保存并从新进程exact resume完成后50步；4K、8K、16K、32K和64K另外各完成10个optimizer steps，128K已由上述100步覆盖。门禁必须同时证明：

- 三张卡均参与；
- 无OOM、NaN、Inf和silent step skip；
- remap正确，PAD/N的ignore逻辑正确；
- 正反向和checkpoint恢复后的loss在容差内一致；
- sampler恢复后没有重复anchor；
- 100步内无OOM、NaN、Inf、显存持续增长或silent retry，peak reserved memory不超过38 GiB；
- sustained tokens/s、每context step time、RC额外开销、checkpoint I/O和预计总时长来自真实测量；
- central output对距离超过32K的远端碱基存在非零梯度/干预响应；同一locus的nested-window、remote-flank mask/shuffle和counterfactual replacement证明模型真正使用远端上下文，而不是只接受128K张量。

只有门禁通过才允许开始无预定总token上限的正式run。若失败，项目状态为BLOCKED，不能改成玩具模型后声称完成。

### 8.4 Checkpoint和选择

- 每500 optimizer steps原子保存可恢复rolling checkpoint，仅保留最近3个；
- 每2,000 steps在固定development panel上评估，只保留按primary selection score排名最好的3个完整候选checkpoint；
- 永久里程碑改为首次达到`0.25×/0.5×/1×/2×/4×/8×… first_cycle_token_capacity`的exposure-equivalent checkpoint，以及WSD触发点和最终点；没有10%/25%/50%/75%/100%这种依赖预定终点的里程碑；
- formal run前根据可核验公共基线冻结`compute_match_targets`（processed-token和/或FLOPs口径）；首次跨越每个目标时永久保存最近checkpoint，专供compute-matched辅助轨，不参与WSD触发或winner选择；无法统一tokenizer/FLOPs口径的模型明确记为`NOT_COMPUTE_MATCHABLE`；
- checkpoint包含模型、优化器、scheduler、GradScaler状态（如有）、sampler permutation/cursor、数据release hash、代码commit和环境锁；
- development panel使用固定窗口、固定MLM mask、固定RC方向，按context、genus、assembly质量和region分层且全程不变；在线随机loss只作健康监控；
- primary selection score固定为按有效masked ACGT token聚合的`fixed_dev_MLM_NLL`，辅助head指标只作预注册安全/退化诊断，不进入最佳checkpoint选择；若候选score相对差小于0.1%，选择`scheduled_sampling_tokens`更少的较早checkpoint；
- 最终checkpoint只能按上述development score选择，任何下游sealed test、public-test或诊断任务结果不得回流；
- 公开模型只发布一个最终winner及必要的训练receipt。

启动前用完整checkpoint实测单份字节数`S_ckpt`。设已产生的永久exposure里程碑数为`M`、冻结compute-match目标数为`K`，可用空间必须至少覆盖`(3 rolling + 3 best + M milestones + K compute-match + WSD trigger + final + 1 temporary) × S_ckpt × 1.2`；在每个新的倍增里程碑前重新检查容量。所有checkpoint先写同目录唯一临时文件、fsync、完整reload并校验关键tensor/receipt后再原子`os.replace`；新best安全落盘前不得删除旧best。空间不足直接BLOCKED，不能在运行中静默减少可恢复性。

## 9. 自包含训练包

训练服务器不得依赖原始服务器路径。正式 bundle 必须包含：

- 所有 sequence/label/pair shards；
- contig/window/split/taxonomy/provenance manifests；
- 模型和训练代码快照；
- Python/CUDA/PyTorch/Mamba依赖锁；
- 每个文件的SHA-256和字节数；
- 顶层Merkle/root hash或确定性manifest hash；
- bundle内部相对路径，不出现源机器绝对路径；
- 离线验证命令和预期结果；
- 数据来源与许可仅作为来源元数据记录，不形成重复执行Gate。

在隔离目录解包后断网执行：校验checksum、加载随机shard、读取所有context、运行完整330M单步并恢复checkpoint。任何缺失文件、自指清单大小错误或外部路径依赖都阻断传输。

## 10. 训练期监控与停止规则

每个optimizer step记录：`unique_corpus_tokens_covered`、`scheduled_sampling_tokens`、`processed_forward_tokens`和各类`valid_objective_targets`，以及context、属/assembly/region/annotation-status、cycle/restart/exposure、各损失numerator/denominator、各目标梯度范数、学习率、tokens/s、step time、峰值allocated/reserved显存、sampler cursor和数据错误计数。

停止条件：

- 任一rank出现NaN/Inf、数据hash漂移或cursor回退；
- 同一pool同一coverage cycle内精确重复anchor计数大于0，或cycle/cursor回退；
- 训练进程世界大小变化后仍继续写同一run；
- 持续数据损坏、标签越界或remap失败；
- `fixed_dev_MLM_NLL`相对历史最佳恶化超过20%且连续两个2,000-step评估均成立时，视为数值/数据异常，保存诊断checkpoint并硬停止；不读取sealed test“找最好点”。

正式run没有累计token上限，但必须有冻结的科学停止规则：只有首轮全部强制pool完成coverage cycle 1（或形成冻结的容量deficit）、且至少完成20,000 optimizer steps后，才允许判断停滞。若连续5次固定development评估中，全局`fixed_dev_MLM_NLL`相对历史最佳改善均小于0.1%，并且32K/64K/128K三个预注册长context stratum均无至少0.2%的改善，则在该评估点原子保存`WSD_TRIGGER`并进入固定10,000-step decay。另一个触发条件是连续3次评估出现online train MLM NLL继续改善、而fixed development NLL相对最佳恶化至少0.5%的过拟合趋势；它同样只触发WSD decay，不打开sealed test。

WSD decay一旦启动不得返回stable段、修改patience或延长衰减；完成10,000步后停止训练。最终winner从全部development候选中按冻结的`fixed_dev_MLM_NLL`选择；sealed pretraining test和任何下游test都不参与触发、延长、停止或winner选择。若停滞条件长期不满足，训练继续，累计token/step不设上限，但每20,000 steps必须发布一次仅基于train/development的暴露、泛化和计算报告。

允许自动恢复的只有明确的硬件/调度中断，且必须从完整checkpoint继续同一个run。数值错误、代码变化或数据变化必须创建新的正式run identity，不能覆盖旧receipt。

## 11. 从数据到论文的唯一执行顺序

1. 冻结下游task registry、primary endpoints、独立单位和clean-inductive/label-transfer轨道，只向语料构建器暴露身份hash；
2. 重新解析原始植物池并冻结十字花科来源清单；
3. assembly/contig QC、精确去重、近重复和orthogroup/LD/haplotype组件聚类；
4. 根据下游防火墙构建exposure-aware cluster split和sealed身份清单；
5. 建立单份sequence store、label store、window/pair catalog；
6. 窗口QC、重叠anchor、per-base coverage及六个context的容量/混杂审计；
7. 冻结各pool的coverage-cycle排列、跨cycle复用上限/deficit规则、长期context比例、task/exposure bindings和数据release hash；
8. 完成330M模型、DDP、精确归一化、checkpoint和完整100-step 128K语义/硬件验收；
9. 启动一条无预定总token/step上限的连续正式run；
10. 只用冻结development条件触发WSD decay，并按固定development MLM NLL选择最终checkpoint；
11. 冻结winner、head和全部seed后执行下游及一次sealed test；
12. 发布一个最终模型、完整方法、机器receipt和真实结果。

任何一步不通过都停在该Gate，不用“测试版”“先缩小跑通”替代最终合同。
