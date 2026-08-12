# BrassicaceaeGenomeFM：完整研究设计、模型、数据、训练与下游评测说明

> 文档性质：最终执行设计说明，不是结果报告。
> 设计修订日期：2026-08-03（CST，UTC+08:00）。
> 当前科学状态：`DESIGNED / NOT EXECUTED`。尚未构建新的十字花科数据release，尚未实现模型，尚未开始GPU训练或下游评测。
> 目标模型：`BrassiCaduceus-330M`。
> 配套文件：本Markdown与同名Word文档内容一致；更细的执行合同分别见`TRAINING_PLAN.md`、`MODEL_ARCHITECTURE.md`、`DOWNSTREAM_TASKS.md`和`TRAINING_PROGRESS.md`。

---

## 1. 先说明哪些是事实、哪些是设计

这份说明故意把“已经看到的数据”“冻结的计划”“最低执行门槛”和“尚未知的结果”分开。这样做不是保守措辞，而是防止把目标数字写成已经完成的科研结果。

- **已核验事实（VERIFIED）**：外部只读植物原始池当前有1,983个顶层assembly目录、1,966个候选genome文件和575个候选annotation文件；它们是广义植物原始池，不等于十字花科有效数据。
- **当前真实数据状态（N/A）**：新项目已经接受的Brassicaceae assembly数、去重后碱基数、六种长度的真实可用窗口数、训练/验证/测试实际容量均尚未产生，不能沿用旧项目数字。
- **冻结的连续训练合同（DESIGN TARGET）**：正式run不设置预定的累计token或optimizer-step上限；首轮优先覆盖未见anchor，每个coverage cycle内部无放回，跨cycle按暴露均衡规则受控复用。训练由固定development收敛/过拟合条件触发WSD衰减并停止，而不是达到某个总token数字后停止。
- **最低执行门槛（GATE）**：每项下游任务必须达到本文件规定的独立单位、阳性数、类别覆盖和数据来源要求；达不到就标记为`INFEASIBLE_FOR_CONFIRMATORY`，而不是用弱标签硬做。
- **性能结果（N/A）**：目前没有任何模型分数，也不能提前声称已经超过AgroNT、PlantCAD2、Nucleotide Transformer或Evo 2。

本文的目标，是把“如何得到可信结果”说清楚，而不是预写一个漂亮结论。

---

## 2. 核心研究问题与论文主线

### 2.1 为什么需要十字花科专属基础模型

现有DNA基础模型大致分成三类。第一类是以Nucleotide Transformer为代表的多物种通用模型，它们覆盖广，但训练语料主要服务人类或一般分子表型，NT-v2-500M的正式模型卡明确说明其850个多物种基因组不包含植物。第二类是AgroNT和PlantCAD2这样的植物专属模型，它们已经证明植物语料能改善调控、表达和跨物种迁移，但目标是整个植物界或被子植物，而不是十字花科内部极其复杂的多倍体、亚基因组和泛基因组问题。第三类是Evo 2一类跨生命域超大模型，具有1 Mb上下文和生成能力，但参数量、训练规模和目标都远超本项目，它并没有显式学习十字花科的U三角、homeolog、S-locus和品质/抗病关系。

十字花科的难点并不只是“多了几个物种”。它同时包含：

1. `Brassica rapa`、`B. nigra`、`B. oleracea`与`B. juncea`、`B. napus`、`B. carinata`组成的U三角二倍体—异源多倍体关系；
2. 古老的全基因组三倍化、后续拷贝保留/分馏和亚基因组优势；
3. homeologous exchange、gene conversion、PAV、SV和TE介导的复杂结构变化；
4. 高度多态、长程连锁的S-locus自交不亲和系统；
5. 硫代葡萄糖苷、油用品质、春化开花、clubroot/blackleg抗性和NLR簇等家族特色性状；
6. 大量任务必须同时使用单碱基精度和数十至上百kb上下文。

因此，本项目不是把“植物模型”简单改名为“十字花科模型”，而是要建立一个能在公共任务上保持竞争力、又能在上述家族专属问题上提供新增能力的统一DNA骨干。

### 2.2 六个预注册研究假设

- **H1 通用能力**：在PGB、PlantCAD2兼容任务、结构边界、表达和变异效应等公共植物任务上，330M级模型应达到强植物公共模型的非劣水平，而不是只在自定义任务上有效。
- **H2 单碱基结构能力**：结构辅助预训练应改善跨物种start/stop、splice donor/acceptor和多标签基因组分割，尤其是在少量标注下。
- **H3 超长上下文能力**：32K、64K和128K应在远端调控、TE邻域、S-locus、NLR簇和SV/PAV任务上提供超过8K裁剪的可重复增益；仅能接收128K张量不算通过。
- **H4 多倍体关系能力**：homeolog/ortholog配对目标应改善U三角来源判定、homeolog检索、表达偏倚和WGT后保留/分馏。
- **H5 十字花科复杂区域能力**：模型应在未见haplotype clan、未见orthogroup、未见cultivar或未见属上优于通用DNA模型、植物模型和简单序列规则。
- **H6 样本效率**：在目标属只有1%、5%和10%标注时，预训练模型应比随机初始化和公共模型获得更高的学习曲线面积，而不是只在100%标签下依靠大head取胜。

### 2.3 能支持和不能支持的主张

全部数据门禁、强基线重跑、五个下游seed和一次sealed test完成后，可以主张“构建并验证了十字花科专属超长DNA基础模型系统”。没有同架构、同QC、同token预算的广义植物语料对照时，不能把增益因果归于语料；架构、平衡、辅助目标和上下文也同时改变。当前仅有一条完整预训练lineage，五个下游seed不代表五个预训练seed。

---

## 3. 与关键公共模型的逐项比较

### 3.1 核验后的关键基线事实

| 模型 | 公开状态与来源 | 参数/骨干 | token与上下文 | 预训练数据和目标 | 最强之处 | 对本项目专属任务的已知边界 |
|---|---|---|---|---|---|---|
| AgroNT | Communications Biology 2024，[DOI](https://doi.org/10.1038/s42003-024-06465-2)；[权重](https://huggingface.co/InstaDeepAI/agro-nucleotide-transformer-1b) | 约1B Transformer；40层、hidden 1500、20 heads | 非重叠6-mer；1024/1025 tokens，约6.1 kb | 48种、主要为可食用植物；约10.5M片段；315k updates、1.5M tokens/update、报告472.5B processed tokens；MLM | PGB八类任务、调控注释、启动子/终止子强度、染色质、组织表达和变异评分 | k-mer使单碱基变异和精确边界解释较困难；单次上下文约6 kb；无U三角/homeolog配对目标 |
| PlantCAD2-S/M/L | 2025 bioRxiv预印本，[DOI](https://doi.org/10.1101/2025.08.27.672609)；[HF集合](https://huggingface.co/collections/kuleshov-group/plantcad2-67e437e241a382671371a572) | 文中S/M/L约88M/311M/694M；Mamba2+Caduceus+RC设计 | 单碱基；8,192 bp | 65个被子植物；以基因中心±5 kb区域切成8,192 bp、stride 4,096窗口；240k steps、global batch 2,048、MLM | 当前最关键植物基线；12项zero-shot及7项微调任务；跨物种调控、表达、翻译和SV表现强 | 预训练窗口以基因附近为主，非全基因组；8 kb不能在一次forward内同时观察相距数十kb的证据；未显式学习十字花科多倍体配对 |
| PlantCaduceus/PlantCAD | PNAS 2025，[DOI](https://doi.org/10.1073/pnas.2421738122)；[权重](https://huggingface.co/kuleshov-group/PlantCaduceus_l32) | 20M–225M；最大l32约225M；Caduceus/Mamba | 单碱基；正式论文任务主要使用512 bp | 16个被子植物；MLM | 单碱基、RC和跨植物迁移；start/stop/splice及变异任务 | 512 bp无法覆盖长程调控、完整S-locus、NLR簇和多数SV背景 |
| GPN-Brassicales | PNAS 2023，[DOI](https://doi.org/10.1073/pnas.2311219120)；[权重](https://huggingface.co/songlab/gpn-brassicales) | 65,880,071参数；25层dilated ConvNet、hidden 512 | 单碱基；512 bp | Arabidopsis和另外7个Brassicales；MLM | 与本项目最近域的变异效应专家，Arabidopsis变异任务必须比较 | 短上下文、卷积骨干、主要为variant scoring；不直接解决成对homeolog、S-locus长区间或结构事件 |
| NT-v2-500M | Nature Methods 2025，[DOI](https://doi.org/10.1038/s41592-024-02523-z)；[权重](https://huggingface.co/InstaDeepAI/nucleotide-transformer-v2-500m-multi-species) | 精确498,346,364参数；29层Transformer、hidden 1024、16 heads | 6-mer；2,048 tokens，理论约12.3 kb | 850个多物种基因组，模型卡明确排除植物和病毒；174B nt/约29B corpus tokens；训练900B processed tokens；MLM | 强通用表征和成熟的标准benchmark | 植物语料缺失；6-mer；没有植物多倍体关系；对本项目仍是必须的通用负控和迁移基线 |
| Evo 2 | Nature 2026，[DOI](https://doi.org/10.1038/s41586-026-10176-5)；[代码](https://github.com/ArcInstitute/evo2)；[7B权重](https://huggingface.co/arcinstitute/evo2_7b) | 1B/7B/20B/40B公开系列；StripedHyena 2 | 单碱基byte token；7B/20B/40B可到1M上下文 | OpenGenome2约8.8T碱基；7B报告2.4T训练tokens，40B报告9.3T；next-token autoregressive | 通用长上下文、变异评分和生成；唯一能在原生长度上覆盖本项目全部128K任务的通用强基线 | 体量和训练数据远大；目标是跨生命域而非植物；单向因果目标对需要双侧信息的中心位点任务不天然对称；大模型微调成本高 |
| BrassiCaduceus-330M | 本项目，尚无权重 | 骨干330,985,472；含预训练heads总331,661,083；47层双向tied-projection Mamba | 单碱基；4K/8K/16K/32K/64K/128K同一run | 仅重新审计的Brassicaceae核基因组；无预定总token上限；coverage-cycle受控复用；MLM+结构+RC+homeolog | 十字花科全基因组、单碱基、128K、关系监督和严格防泄漏任务体系 | 参数远小于Evo 2；最终processed-token/FLOPs规模训练后才知道；没有生成目标；优势必须真实验证 |

PlantCAD2论文内部有一个需要在正式比较时处理的数字差异：摘要写“676M”，正文、图注和公开S/M/L系列写约88M/311M/694M。正式重跑不采用摘要四舍五入数，而是锁定具体Hugging Face revision，并由加载后的`sum(p.numel())`生成参数receipt。与本模型最有解释力的两个PlantCAD2对照是约311M的M版本（规模匹配）和约694M的L版本（最强公开植物版本）。

不同模型报告的“token”不能直接横比。AgroNT和NT使用6-mer，Evo 2、本模型和PlantCAD2使用单碱基；“unique corpus bases”“有放回或多epoch处理的tokens”和“实际forward tokens”也不是同一分母。因此正文必须并列报告参数、tokenizer、unique数据容量、processed tokens和上下文，不能只用一个最大数字说明规模。

### 3.2 我们不靠避开基线取胜

公共任务分三条比较轨道：

1. **官方复现轨道**：按PGB、PlantCAD2或原论文公开输入长度、split和指标重跑，检验实现是否与公开趋势相符。
2. **相同任务合同轨道**：同一DNA、同一train/development/test、同一负例、同等head/PEFT参数预算和同样五个seed；每个模型使用预注册的实际可见长度。
3. **原生能力轨道**：允许模型使用自己的最长上下文。短模型中心裁剪并明确“可见6 kb/8 kb/512 bp”，Evo 2可读取完整128K；该轨道评价实际系统能力，不假装只看512 bp就是公平的长程比较。

在一般任务上，目标是对最强公共植物模型达到预注册非劣界限；在十字花科专属任务上，目标是超过`max(AgroNT, PlantCAD2-L, PlantCaduceus, GPN, Evo2-7B及任务专家)`中实际可执行的最强者。这里的“目标”不是预写结果，任何未超过都如实报告。

---

## 4. 数据总体设计

### 4.1 原始来源与当前状态

当前只确认项目外部只读路径`/home/user/zhangzhishuai/data/plantDB/genome`存在广义植物数据。新的Brassicaceae清单必须从这里重新解析，并逐条绑定上游稳定来源。候选来源优先顺序是NCBI Assembly/GenBank或RefSeq、Ensembl Plants、Phytozome及原始论文资源；本地文件名本身不能作为来源证明。

每个最终纳入assembly必须记录：

- source accession、物种、材料/品种/生态型、NCBI Taxonomy ID；
- assembly版本、核型/倍性、单倍型或亚基因组状态；
- FASTA、GFF3和重复注释的上游URL/数据库/抓取日期；
- 原文件字节数和SHA-256；
- source sequence hash与规范化ACGTN hash；
- 许可仅作为来源元数据，不作为重复询问的执行门槛；
- 质量、污染、注释和是否进入结构监督的receipt。

当前已接受assembly数仍为`N/A（实际为尚未接受任何新release成员）`。只有taxonomy和QC完成后才能填入物种数、属数、二倍体/多倍体比例和真实碱基量。

### 4.2 纳入与排除

主体预训练只使用taxonomy明确属于Brassicaceae的核基因组。染色体级/高连续性assembly优先；同一材料多版本只留质量最优者。具有明确生物意义的不同品种、单倍型和泛基因组路径可以保留，但进入近重复簇并限制权重。

排除：叶绿体、线粒体、质粒、明显病原/微生物污染、taxonomy冲突、版本无法追溯、核基因组N比例超过5%、明显重复发布且无独立生物意义、坐标与FASTA不一致的结构标签。低质量注释不一定排除DNA，但不能进入结构监督真值。

### 4.3 六层数据对象

1. **source/assembly层**：来源、版本、taxonomy、材料、倍性和总体QC。
2. **contig层**：只编码一次的canonical ACGTN序列、坐标、长度和局部可用性。
3. **similarity cluster层**：assembly/contig/窗口近重复及不可拆分split组件。
4. **anchor层**：相互覆盖超过80%的候选窗口归为同一anchor；每个coverage cycle内最多消费一次，跨cycle暴露单独记账。
5. **window层**：一个anchor只选择4K–128K中的一种正式长度，携带region、QC和split字段。
6. **label/pair层**：逐碱基结构标签、高可信ortholog/homeolog关系以及有效性mask；标签和DNA分开存储但共享release ID。

### 4.4 QC和去重

Assembly receipt至少包含总长度、contig数、N50/L50、最大contig、N比例、GC、非ACGTN字符、BUSCO、污染、预期基因组大小偏差和注释可用性。窗口重新计算`N_fraction <=1%`、不得有连续≥32 bp的N、不得跨contig、非法字符为0，并记录低复杂度、TE和区域类型。

去重顺序是：真实序列hash的assembly/contig exact去重；`min(sequence, RC(sequence))`窗口exact去重；重叠anchor；MinHash候选加ANI/局部比对确认的近重复聚类。ANI≥99.9%且覆盖≥90%的assembly默认实质重复；99.5%–99.9%同簇；跨split窗口若identity≥98%且覆盖较短窗口≥80%，必须并簇或移出评估。

### 4.5 训练、development、sealed test和迁移外群

相似性簇是不可拆分单位，容量目标约90%/5%/5%，不是随机切窗口：

- **train**：预训练参数更新；无预定累计token上限。首轮unique容量由新release实测，后续processed exposure通过coverage cycle受控增加。
- **development split**：只用于固定MLM panel、训练诊断和checkpoint选择；不参与参数更新。
- **sealed pretraining test**：winner冻结后一次性评估预训练语言建模能力。
- **保留acceptance split**：bundle中有4,320个旧设计窗口；正式v1代码不读取、不训练、不报告其结果，保持sealed/unused。
- **runtime GPU acceptance**：不是额外数据split；step 1前只读正式train bundle的确定性ordinal，以零学习率临时optimizer验证真实128K执行几何，不推进sampler或权重。
- **Brassicales外群和整属留出**：不参加Brassicaceae主体预训练，用于true genus/species holdout和迁移。

下游任务拥有独立的orthogroup、cultivar、study、LD block、haplotype clan、SV component或染色体block split。预训练90/5/5不能替代下游防泄漏。

### 4.6 预训练窗口长度和长期混合比例

每个optimizer step固定调度786,432个`scheduled_sampling_tokens`，所以不同长度的全局窗口数不同。正式训练没有总step或总token上限；长期比例固定为9.5%/19.0%/19.5%/25.0%/21.0%/6.0%，由累计token缺口调度器从第一步持续维持。

下表使用10,000个optimizer steps作为方便核验的参考记账块。它不是训练阶段、训练上限或停止点；真实run跨过记账块时模型、优化器、scheduler、sampler cycle和全局step都连续。

| context | 长期token比例 | 全局窗口/step | 每10,000步参考steps | 参考窗口数 | 参考scheduled tokens |
|---:|---:|---:|---:|---:|---:|
| 4,096 | 9.5% | 192 | 950 | 182,400 | 747,110,400 |
| 8,192 | 19.0% | 96 | 1,900 | 182,400 | 1,494,220,800 |
| 16,384 | 19.5% | 48 | 1,950 | 93,600 | 1,533,542,400 |
| 32,768 | 25.0% | 24 | 2,500 | 60,000 | 1,966,080,000 |
| 65,536 | 21.0% | 12 | 2,100 | 25,200 | 1,651,507,200 |
| 131,072 | 6.0% | 6 | 600 | 3,600 | 471,859,200 |
| **合计** | **100%** | — | **10,000** | **547,200** | **7,864,320,000** |

窗口数随长度下降是正常现象；训练权重按token和有效标签数归一化，不能按“窗口条数”平均。首个coverage cycle中，每step调度的primary tokens属于首次anchor暴露；进入后续cycle后仍增加`scheduled_sampling_tokens`，但不再增加已经覆盖过的`unique_corpus_tokens_covered`。5%的anchor额外计算RC第二视图，增加`processed_forward_tokens`和forward compute，不增加primary scheduled tokens。

固定development panel每次评估处理50,331,648个forward tokens。由于正式run没有固定评估次数，不再预写“development总共占训练百分之多少”；每次及累计development开销都在训练日志中单独记账。Development/test split中未进入固定panel的容量作为冻结储备，不得在看过结果后反复抽新panel挑checkpoint。

### 4.7 固定development、sealed test与acceptance窗口

| 数据用途 | 4K steps/窗口 | 8K | 16K | 32K | 64K | 128K | 合计窗口 | 合计tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 固定development panel | 6 / 1,152 | 12 / 1,152 | 13 / 624 | 16 / 384 | 13 / 156 | 4 / 24 | 3,492 | 50,331,648 |
| 一次性sealed pretraining test | 12 / 2,304 | 24 / 2,304 | 25 / 1,200 | 32 / 768 | 27 / 324 | 8 / 48 | 6,948 | 100,663,296 |

bundle另保留4,320个、117,964,800 tokens的旧设计acceptance窗口；正式v1不为其建运行索引，也不读取或报告结果。Development panel使用固定窗口、固定mask和固定RC方向，每2,000 steps评估一次。Sealed pretraining test只在winner按development NLL确定后读取一次。正式torchrun在step 1之前执行一次不参与模型选择的最坏几何硬件验收：真实128K primary、强制RC、每rank 2对homeolog、反向、梯度裁剪和零学习率临时AdamW；PASS后销毁临时optimizer并创建全新正式optimizer。该验收只证明当前执行几何可运行，不替代development或sealed test证据，也不产生训练step。

### 4.8 数据release的物理组成

- `sequence_store`：uint8/mmap，A/C/G/T/N各一个ID；每条contig只存一次；IUPAC原字符放稀疏sidecar。
- `contig_index`：assembly、contig、全局offset、长度、taxonomy、source和hash。
- `window_catalog`：window/anchor、坐标、长度、QC、区域、split、similarity cluster和sampling priority。
- `label_store`：9个region、frame、6个boundary及validity mask。
- `pair_catalog`：高可信syntenic ortholog/homeolog和hard-negative排除信息。
- `task_registry`与`pretraining_exposure_matrix`：下游测试身份hash及预训练暴露状态。
- `provenance`与checksum manifest：文件字节数、SHA-256、工具版本和顶层root hash。

所有数据通过自包含bundle迁移；GitHub只放轻量设计文档，不上传原始数据、shard、标签、日志或checkpoint。

---

## 5. 模型架构

### 5.1 输入和词表

模型按单碱基输入，不使用6-mer、BPE或codon token。词表为`PAD, A, C, G, T, N, MASK, RESERVED`共8个token。底层store使用`A=0,C=1,G=2,T=3,N=4`，DataLoader必须显式`+1`；否则A会被误当PAD。N和PAD可以作为上下文，但不作为MLM有效target。

六种长度分别是4,096、8,192、16,384、32,768、65,536和131,072 bp。训练按同长度bucket形成batch，不依赖大面积padding。模型没有固定绝对位置表，顺序由Mamba状态递推和局部卷积编码。

### 5.2 47层双向tied-projection Mamba

冻结配置：`d_model=1024`、47层、expansion=2、`d_inner=2048`、`d_state=16`、`d_conv=4`、`dt_rank=64`、RMSNorm `eps=1e-5`、dropout=0、FP32 residual accumulation。

每层用同一输入分别做前向和反向Mamba。反向分支读倒序序列，输出再倒回原坐标，然后与前向结果逐元素相加。两个方向共享参数主体`in_proj/out_proj`，但SSM、depthwise convolution和时间参数独立。这样比两个完全独立骨干节省参数，同时保留不同方向动力学。

它不是Transformer：128K全注意力的`L×L`矩阵在3×40GB A100上不现实；Mamba selective scan对长度线性扩展。模型也不把现有Caduceus方程包装成“全新神经网络”，创新重点在十字花科全基因组语料、结构与homeolog联合目标、128K系统和专属证据体系。

### 5.3 参数量

单层合同为：

`P_layer = 6d² + 8dr + 12dn + 4dk + 13d`

代入`d=1024,r=64,n=16,k=4`，每层7,042,048参数。

| 模块 | 参数量 | 占完整训练图约比 |
|---|---:|---:|
| 47层Mamba blocks | 330,976,256 | 99.7935% |
| 8-token embedding | 8,192 | 0.0025% |
| final RMSNorm | 1,024 | 0.0003% |
| **骨干合计** | **330,985,472** | **99.7963%** |
| tied MLM bias | 8 | <0.0001% |
| 9通道region head | 9,225 | 0.0028% |
| 4类frame head | 4,100 | 0.0012% |
| 6类boundary head | 6,150 | 0.0019% |
| 1024→512→256 contrastive head | 656,128 | 0.1978% |
| **预训练heads合计** | **675,611** | **0.2037%** |
| **完整预训练计算图** | **331,661,083** | **100%** |

“330M”是骨干级命名。正式实现加载后必须逐tensor重算并与331,661,083一致；若库实现引入偏差，训练前更新参数合同，不能训练后再解释。

### 5.4 RC策略

模型不采用显存更高的RCPS双通道激活，而采用：每个anchor以0.5概率输入正向或反向互补；5%的anchor同时计算两个方向并用逐位置cosine一致性；下游将`x`和`RC(x)`预测坐标/标签重映射后平均。它可以称RC-consistent/RC-conjoined，不能称结构上严格RC等变。

### 5.5 五类输出接口

- MLM logits：逐碱基8类；权重与embedding共享。
- Region：gene、exon、intron、CDS、5'UTR、3'UTR、ncRNA、TE、实验支持promoter九个可重叠通道。
- Frame：frame0/1/2/non-CDS；冲突isoform位置ignore。
- Boundary：splice donor/acceptor、start/stop、TSS/TTS六个稀疏通道。
- Homeolog embedding：基因体及上下游mask-aware pooling后投影为256维L2归一化向量。

下游可读取逐碱基hidden、全窗口masked mean、多尺度分块pool和gene-anchor三段pool。公共模型同时评估官方pooling和统一mean pooling，不能故意给对手选择较差读取方式。

---

## 6. 六个预训练目标

总损失固定为：

`L = L_MLM + 0.25 L_region + 0.10 L_frame + 0.10 L_boundary + 0.05 L_RC + 0.05 L_homeolog`

### 6.1 MLM：基本序列语法

从ACGT中选15%目标。80%替换MASK，10%替换随机ACGT，10%保持。目标预算一半是单点，一半为长度1–10、`p=0.35`的截断几何span；span不跨N/PAD/contig边界。作用是同时学习motif、局部语法和长程条件依赖。

### 6.2 Region：可重叠植物结构

九通道`BCEWithLogits`只在标签有效位置计算。正式v1冻结uniform 1.0通道权重；不可调用通道由valid-mask忽略。region不是互斥softmax，因为exon可以同时属于gene/CDS/UTR层级，TE也可能插入基因区域。

### 6.3 Frame：编码相位

高可信CDS中做四类cross-entropy；strand、phase或isoform冲突位置ignore。该任务迫使模型学习三碱基周期与转录方向，但不会把低质量GFF的错误相位当真值。

### 6.4 Boundary：稀疏边界

六个独立sigmoid通道使用focal loss `gamma=2`、冻结`alpha=0.25`，只在该来源可调用的通道上计算；缺失实验TSS/TTS不会被伪造为负例。缺少实验TSS/TTS的“上游2 kb”只能是proxy，不算直接标签。

### 6.5 RC一致性：方向稳定

对5%的anchor同时计算正向/RC，逐有效位置对齐、L2归一化后优化`1-cosine_similarity`。PAD、N和ignore不进入分母。RC额外forward必须计入吞吐和ETA。

### 6.6 Homeolog/ortholog：十字花科关系监督

正式v1对4K高可信共线窗口使用256维双向multi-positive InfoNCE，temperature固定0.07。每rank每个optimizer step从positive-edge池确定性取2对，三个rank的edge ordinal互不重叠；同一orthogroup是正例而不是负例。pair视图增加processed-forward token账，不冒充主语料unique exposure。

positive-edge池使用cycle内不放回的仿射全排列；cycle、cursor、tail轮转和exposure进入完整checkpoint。这个实现优先保证当前3×40GB A100的显存闭合与可恢复性；跨rank超大negative bank属于后续新run合同，不能在正式v1中动态启用。

### 6.7 目标支配门禁

正式run中loss权重不动态调整。启动前preflight固定loss常量与代码hash；训练逐step记录六个目标的loss、有效分母和global gradient norm，非有限值立即终止。任何权重修订都必须生成新run identity，禁止依据development/sealed test边跑边调。

---

## 7. 正式训练设计

### 7.1 三卡batch

3进程DDP，每GPU每micro-step固定131,072个primary sampling tokens：4K×32、8K×16、16K×8、32K×4、64K×2、128K×1。三卡合计393,216 tokens，gradient accumulation=2后每optimizer step固定调度786,432个`scheduled_sampling_tokens`。首个coverage cycle内它们也是首次anchor暴露；后续cycle不再称为unique。六个目标按跨micro-batch、跨rank的全局有效分母归一化，不能把一个4K窗口和一个128K窗口等权。

### 7.2 coverage cycle、受控复用和数据平衡

正式run不设置累计token或step上限。六个context各有一个覆盖全部train窗口的确定性仿射全排列pool；cycle内部严格无放回，三rank在同一optimizer step取得互不重叠的ordinal。pool尾不足一个完整全局batch时显式记入rotated-tail账并进入下一cycle，绝不静默复制。首个cycle优先覆盖从未使用anchor，pool耗尽后才进入受控复用。

跨cycle允许受控复用，但新的动态MLM mask和RC方向不把来源坐标重新记成unique。训练同时记录：首次anchor暴露的`unique_corpus_tokens_covered`、每步固定增加的`scheduled_sampling_tokens`、包含RC与homeolog额外视图的`processed_forward_tokens`以及六个目标各自的`valid_objective_targets`。另报告每context cycle/cursor、rotated tail和exact repeat；不把动态训练称为若干严格epoch。

长期token比例为4K/8K/16K/32K/64K/128K=`9.5/19/19.5/25/21/6%`，由跨step累计token deficit scheduler实现。正式v1不额外施加taxon/source上限；每个来源在首轮的总暴露与其通过QC和去重后留下的唯一窗口容量一致。属、物种和assembly组成由冻结catalog离线统计，不能把自然容量比例误写成均匀物种采样。

### 7.3 优化器与WSD学习率

bf16参数/激活、FP32 residual、AdamW `betas=(0.9,0.95)`、`eps=1e-8`、weight decay 0.1、global grad clip 1.0、dropout 0。采用WSD（Warmup–Stable–Decay）：前1,000 optimizer steps从0线性warmup到`3e-4`；stable段保持`3e-4`且不预设结束step；冻结development停滞或过拟合条件触发后，执行固定10,000-step cosine decay到`3e-5`并停止。RC第二视图增加processed forward tokens，但不让scheduler额外前进。

### 7.4 128K显存设计

331,661,083个训练参数按约16 bytes/parameter的保守状态预算约4.94 GiB。单条128K的1024维bf16 hidden约0.25 GiB，FP32 residual约0.50 GiB；若47层逐层保留hidden+residual边界，理论约35.25 GiB，所以“逐层checkpoint”不够。

正式实现把47层按连续组做non-reentrant activation checkpoint，并把head loss按8,192位置分块计算。每组4、5、6层是同一冻结代码身份下的允许候选，launcher默认5，并把实际选择绑定到preflight、128K acceptance和永久checkpoint；显存不足可直接改候选值重启，不改模型参数或数据身份。正式v1默认3进程DDP；FSDP full-state保存/重分片恢复代码已实现，但不能在同一checkpoint lineage中静默切换。不能缩模型、截断128K或把128K切成互不通信短块后继续使用原名称。

### 7.5 Checkpoint与winner

每500 steps原子保存rolling checkpoint，仅留最近3个；每2,000 steps在固定development panel评估并只保留best 3。永久里程碑为`0.25×/0.5×/1×/2×/4×/8×… first-cycle exposure-equivalent`、WSD触发点和最终点，不再使用依赖预定终点的10%/25%/50%/75%/100%。Formal run前还要冻结可核验公共基线的processed-token/FLOPs目标，首次跨越时永久保存compute-matched checkpoint；它们只参加公平预算辅助轨，不参与WSD或winner选择。Winner只按`fixed_dev_MLM_NLL`选择；辅助heads仅作退化诊断。若score差<0.1%，选择scheduled sampling tokens更少的checkpoint。下游test、公共test和sealed pretraining test都不能选checkpoint或触发停止。

### 7.6 停止规则

NaN/Inf、数据hash漂移、sampler cycle/cursor回退、同cycle重复anchor>0、world-size变化后继续写原run、标签越界或remap失败均硬停止。Fixed development NLL相对历史最佳恶化>20%并连续两个评估成立时，按异常硬停止，不打开sealed test“找最好点”。

科学收敛判断只有在首轮全部强制pool完成coverage cycle 1或形成冻结deficit，且全局step≥20,000后才启用。若连续5次development评估中，全局fixed-dev NLL改善均<0.1%，并且32K/64K/128K三个长context stratum均无≥0.2%改善，则保存`WSD_TRIGGER`并进入10,000-step decay。若连续3次出现online train NLL继续改善而fixed development NLL相对最佳恶化≥0.5%，也触发decay。Decay一旦开始不得撤回、延长或修改patience；完成后停止，并仅按fixed development NLL选winner。若条件长期不满足，训练继续，没有累计token/step上限；每20,000 steps发布一次train/development暴露、泛化和计算报告。

---

## 8. 验证、测试和下游数据之间的边界

### 8.1 三条暴露轨道

- **clean-inductive**：下游test的assembly/区域/orthogroup/haplotype及近重复组件从预训练train、development、acceptance和辅助标签全部移除；区域向两侧扩展131,071 bp halo，任何预训练窗口与halo相交即拒绝。
- **label-transfer**：允许目标物种无标签DNA参加MLM，但任务标签、pair和统计量隔离；只能说标签迁移。
- **public-exposure-unknown**：公共模型预训练清单无法完全审计时标记UNKNOWN；不把暴露不对称当成架构胜负。

### 8.2 下游最低通用门槛

除任务专门门槛外，确认性binary任务test至少100个阳性、100个匹配负例和30个最高层独立单位；multiclass至少每类50个独立单位且总数≥300；regression至少300个独立样本和30个最高层cluster；retrieval至少500个query、100个未见family且每个query有≥20个候选。Base-level数量很大也不能替代assembly、orthogroup、study或haplotype独立性。

### 8.3 标签质量层级

- `DIRECT`：功能验证、实验peak、严格pangenome事件、核验边界、可靠表达定量；可进入主分析。
- `STRONG_INFERENCE`：fine-mapping credible set、跨工具一致且有独立证据；可进入主分析但分层。
- `PROXY`：普通GWAS峰、选择扫描、启发式promoter、单一预测软件；只作探索或敏感性。
- `UNKNOWN/CONFLICT`：不作为0，必须ignore。

---

## 9. 公共任务：必须覆盖其他基因组模型已有能力

### P1 调控序列分类

**问题**：基础表征能否识别promoter、enhancer、TF binding、histone mark和开放染色质。**来源**：GUE/NT公开任务、PGB和可核验植物ATAC/ChIP数据。**输入**：按官方长度复现；本项目统一轨道以4K为主。**split**：染色体block、assembly cluster和重叠peak成组。**负例**：同GC、长度、repeat、距TSS和callable背景。**head**：冻结骨干线性probe和同预算PEFT。**主指标**：AUPRC；MCC和macro-F1为辅。**基线**：DNABERT-2、NT-v2-500M、AgroNT、PlantCAD2、PlantCaduceus、CNN。该任务证明通用能力，不作为十字花科创新。

### P2 AgroNT/PGB八类兼容任务

正式复现PGB的polyadenylation、splice site、lncRNA、promoter strength、terminator strength、chromatin accessibility、gene expression和enhancer八类任务。公开数据来自[PGB Hugging Face release](https://huggingface.co/datasets/InstaDeepAI/plant-genomic-benchmark)。先做官方split复现，再构建物种/属留出的严格split。输入长度保持原始400/398/101–6000/170/170/1000/6000/1000 bp合同。主比较是AgroNT、PlantCAD2-M/L、本模型和任务专家；NT与DNABERT-2作为通用基线。官方结果与严格结果不合并。

### P2B PlantCAD2兼容任务

覆盖其12项zero-shot和7项微调范式：跨物种conservation、TIS/TTS、splice donor/acceptor恢复、core/non-core junction conservation、SV effect、跨物种ACR、92 cell types ACR、表达on/off与回归、翻译on/off与回归。数据优先使用其[公开集合](https://huggingface.co/collections/kuleshov-group/plantcad2-67e437e241a382671371a572)和代码定义；先复现8,192 bp合同，再增加Brassicaceae整属留出。PlantCAD2-M是近参数匹配基线，PlantCAD2-L是强植物上界。

### P3 翻译和剪接边界迁移（确认性）

**训练/测试**：Arabidopsis或注释丰富train物种训练，Brassica、Camelina、Cardamine等整属/整物种外测；orthogroup和assembly cluster不跨split。**输入**：4K中心窗口，并另报16K/64K上下文。**标签**：start、stop、donor、acceptor直接GFF证据。**hard negative**：同region、同frame、含相似canonical motif但不是真边界。**最低门槛**：每类test阳性≥10,000，至少3个held-out属、500个未见orthogroup和6个assembly clusters。**主指标**：四类boundary macro-AUPRC；±1/±3 bp F1为辅。**基线**：PlantCAD2、PlantCaduceus、GPN、AgroNT、NT、SpliceAI式专家、PWM。结构辅助预训练不算纯zero-shot，必须给self-supervised-only消融。

### P4 单碱基多标签分割（确认性）

**输入**：4K/16K/64K；**标签**：九region、三frame、六boundary和unknown mask；**split**：orthogroup+assembly cluster，整物种外测；**最低门槛**：至少6个held-out assembly clusters、2,000个未见orthogroups，常见region每类≥1M callable test bases，稀疏边界按P3门槛。**主指标**：九region macro-AUPRC；边界、frame和segment IoU为辅。**基线**：PlantCAD2/PlantCaduceus、SegmentNT适配、Helixer、AUGUSTUS、GeMoMa、one-hot U-Net/CNN。

### P5 DNA到表达和RNA coverage

**来源**：版本匹配的公共RNA-seq/PRO-seq数据，GEO/SRA/Expression Atlas accession和处理流程逐study冻结。**输入**：TSS/基因中心32K/64K/128K；DNA-only主榜；tissue/condition只在扩展榜。**标签**：study内规范化TPM或coverage，不能把study批次当生物差异。**split**：orthogroup、accession×study×tissue。**主指标**：Spearman；R²/MAE为辅。**基线**：AgroNT、PlantCAD2、Enformer/Borzoi兼容任务、promoter k-mer。DNA不能解释全部环境表达，性能上限要讨论。

### P6 长程调控、3D和DNALONGBENCH兼容任务

**对象**：enhancer-target、eQTL、TSS activity、Hi-C/3D contact和远端调控。**输入**：32K/64K/128K；**split**：染色体block×study×tissue；**最低门槛**：若没有至少30个独立染色体/study blocks或直接植物标签，则不进入确认性结果。**指标**：任务原始指标及距离分层相关。**基线**：Evo2-7B、Caduceus/HyenaDNA、PlantCAD2、Akita/Enformer等专家。该任务必须配32K-vs-128K消融和远端替换实验。

### P7 变异效应（确认性）

**输入**：ref/alt等长窗口；zero-shot主分数是ref/alt pseudo-log-likelihood差。**来源**：1001 Arabidopsis、可靠Brassica群体变异、实验功能变异、GWAS/QTL fine-mapping；每一层标签分开。**split**：LD block×population×study×chromosome。**负例**：MAF、功能区、callability、距基因和LD匹配。**最低门槛**：≥200个DIRECT/STRONG positives、≥400匹配负例、≥30 LD blocks、≥3独立study。**主指标**：matched callable set AUPRC；微调、top-1% recall和MAF相关为secondary。**基线**：GPN-Brassicales、GPN-MSA、PlantCAD2、PlantCaduceus、AgroNT、Evo2-7B、phyloP/phastCons。

---

## 10. 十字花科专属与复杂区域任务

这些任务被设计为公共模型可以按同一输入合同真实参评，但它们缺少十字花科关系监督、全基因组长窗口或足够领域深度，因而**预期**表现较弱。最终是否较弱必须由sealed test证明，不能在文档里写成既成事实。

### B1 U三角亚基因组来源和homeolog检索（确认性、旗舰任务）

- **对象**：A/B/C二倍体祖先与AB/AC/BC异源多倍体之间的共线关系。
- **输入**：gene body+上下游，4K/16K/64K；禁止输入物种名、坐标和亚基因组标签。
- **标签来源**：版本匹配的高可信共线block、orthogroup和人工核验亚基因组注释。
- **任务**：diploid→polyploid检索、正确homeolog排序、A/B/C来源分类。
- **split**：整个orthogroup+cultivar成组；test必须有未见orthogroup和未见cultivar。
- **hard negative**：同家族非共线拷贝、GC/长度匹配的异亚基因组基因。
- **最低门槛**：六个U三角物种均覆盖；原则上每物种≥2个独立assembly/cultivar；test≥1,000 queries、≥300未见orthogroups，每个来源类≥200 queries。
- **主指标**：未见orthogroup MRR；Recall@1/5/10和来源macro-F1为辅。
- **基线**：BLAST/MMseqs2+synteny、PlantCAD2-M/L、AgroNT、PlantCaduceus、GPN、Evo2-7B、Caduceus、随机初始化。
- **为什么可能形成专属优势**：本模型在预训练中显式看到edge-disjoint homeolog positive和同家族hard negative；公共植物模型没有这一关系目标。但必须用“去掉homeolog loss”消融证明。

### B2 多倍体homeolog表达偏倚（确认性）

- **问题**：仅从成对DNA能否预测同一homeolog pair在组织/条件中的相对表达优势。
- **输入**：pair两侧最大128K；主榜只有DNA；组织/环境embedding单列扩展榜。
- **标签来源**：homeolog-aware唯一比对或可分配read的RNA-seq；低可映射pair剔除。
- **split**：homeolog group、cultivar和tissue-study三重隔离。
- **最低门槛**：≥1,500可靠pair、≥3独立study、≥3组织/条件；sealed test≥300 pairs且每个偏倚类别≥100。
- **主指标**：pairwise accuracy；macro-F1、Spearman和校准为辅。
- **基线**：promoter k-mer、gene/TE距离、PlantCAD2、AgroNT、PlantCaduceus、Evo2、随机初始化。
- **难点**：公共模型可分别编码两个基因，但没有配对关系预训练；短上下文也看不到远端TE和邻域差异。DNA-only不能解释瞬时环境响应，稳定偏倚和条件特异偏倚分层。

### B3 十字花科WGT后的保留与分馏（确认性）

- **标签**：高可信syntenic block中的single/double/triple retention及fractionation；非共线家族扩张不当作同一标签。
- **输入**：祖先/现存同源基因及64K邻域。
- **split**：orthogroup+syntenic block；相邻block同组。
- **最低门槛**：≥900 orthogroups、每类≥100独立test units、≥3个属。
- **主指标**：macro-F1；per-class recall和跨属校准为辅。
- **基线**：synteny统计、基因长度/表达/TE距离logistic、PlantCAD2、AgroNT、GPN、Evo2。
- **专属性**：这是十字花科深层复制历史与局部DNA环境的联合任务，不是普通promoter分类。

### B4 Homeologous exchange与gene conversion（探索性，数据充分后升级）

**输入**：断点两侧32K/64K/128K及祖先参考pair。**标签**：长读长/图泛基因组、coverage和独立比对共同支持的事件。**split**：cultivar×event cluster×chromosome block。**负例**：普通高相似homeolog、组装gap和非交换SV。**指标**：event AUPRC、breakpoint F1、来源macro-F1。**最低升级门槛**：≥300高可信事件、≥50 events/class和≥6 cultivars。短模型无法在一次forward内同时看到远端双侧证据；Evo2是关键长模型对照。该任务只能称候选识别，不能替代细胞遗传验证。

### B5 S-locus自交不亲和（确认性、旗舰任务）

- **输入**：SRK/SCR及完整S-locus邻域，最高128K。
- **标签来源**：核验S-haplotype、dominance class、已发表兼容/不兼容杂交结果；普通序列相似不等于功能标签。
- **split**：S-haplotype clan+accession cluster；近等位序列不得跨split。
- **最低门槛**：总计≥100 accessions、≥30 haplotype clans；sealed test≥10未见clans和≥500独立compatibility pairs。
- **任务**：clan retrieval、功能/优势类、pair compatibility。
- **主指标**：未见clan retrieval MRR；分类/compatibility为secondary。
- **基线**：BLAST/haplotype规则、k-mer、PlantCAD2、AgroNT、PlantCaduceus、GPN、Evo2。
- **为什么重要**：S-locus高度多态且长程连锁，8K/6K模型通常只能看到局部；本模型必须用完整长区域和未见clan证明不是记忆。

### B6 春化、开花和生态适应等位变异（探索性）

围绕FLC、FRI、FT、SOC1、VIN3及扩增拷贝，但不把任务限制为已知基因。输入为ref/alt 64K/128K；标签来自多环境flowering time、vernalization response、功能验证和fine-mapping。split按relatedness cluster×study×environment×主效haplotype。主要指标variant AUPRC、top-k causal recall和表型Spearman。若DIRECT positives少于100或独立study少于3，保持探索性。环境变量只能进扩展榜。

### B7 硫代葡萄糖苷与油用品质（确认性）

- **对象**：glucosinolate通路及油菜油酸、芥酸、蛋白含量等品质调控。
- **输入**：候选基因/变异周围4K–128K。
- **标签**：功能验证、代谢QTL/GWAS fine-mapping和稳定haplotype效应；普通GWAS峰只作proxy。
- **split**：gene family×LD block×cultivar×study。
- **最低门槛**：≥100 DIRECT/STRONG causal positives、≥300匹配负例、≥3研究和≥3性状家族。
- **主指标**：matched causal-variant AUPRC；top-1% recall、效应方向和代谢Spearman为辅。
- **基线**：通路/注释规则、GWAS后验、GPN、PlantCAD2、AgroNT、PlantCaduceus、Evo2。
- **专属性**：把十字花科特色代谢的基因家族、局部变异和长程簇环境连起来，而不是泛化的“功能变异”标签。

### B8 NLR簇与clubroot/blackleg抗性（确认性）

- **输入**：NLR gene、presence/absence或ref/alt，加最长128K邻域。
- **标签**：独立病原接种、图位克隆/功能验证和pathotype-specific resistance；QTL-only单列proxy。
- **split**：NLR orthogroup×resistance locus×pathotype×study。
- **hard negative**：同簇未证实NLR、失活拷贝和结构域相似非抗性基因。
- **最低门槛**：≥100阳性locus-haplotype-pathotype units、≥30独立test loci、≥3 pathotypes和≥3 studies。
- **主指标**：pathotype/study-held-out AUPRC；macro-F1和top-k candidate recall为辅。
- **基线**：NLR-Annotator、结构域/BLAST规则、PlantCAD2、AgroNT、PlantCaduceus、GPN、Evo2。
- **专属性**：复杂NLR簇、PAV和TE背景需要单碱基+长程；模型排序仍不等于发现新抗病基因。

### B9 PAV/SV/TE调控与表型影响（确认性）

- **输入**：断点双侧、插入序列、ref/alt path及128K邻域。
- **标签**：高质量pangenome graph事件；event type、breakpoint和regulatory/phenotypic impact分层。
- **split**：SV cluster×accession×graph component×chromosome block。
- **最低门槛**：≥300具有DIRECT/STRONG impact标签的事件，主要impact类别各≥50，≥3独立pangenome/study来源。
- **主指标**：event-level impact macro-F1；event type AUPRC、breakpoint F1和效应Spearman为secondary。
- **基线**：SV/TE专家注释、alignment/coverage、PlantCAD2、Caduceus/HyenaDNA、PlantCaduceus、Evo2。
- **专属性**：检验模型是否真正使用插入、TE和远端基因环境；只预测SV类型不等于预测影响。

### B10 驯化、改良与适应变异（探索性）

输入64K/128K SNP/indel上下文；标签按功能验证、fine-mapping、GWAS和选择扫描分层，选择扫描不能冒充因果。split为population×LD block×trait study×chromosome。比较GWAS posterior、选择统计、phyloP、GPN/GPN-MSA、PlantCAD2、AgroNT和Evo2。只有≥200强阳性、≥3群体和≥3研究后才升级确认性。

### B11 十字花科基因簇边界与协同调控（探索性）

对象是glucosinolate、NLR、次生代谢及串联复制簇；输入32K–128K；标签为共线保守block、共表达模块、实验调控和结构边界；split按整个cluster family。任务是boundary segmentation、成员功能和pair co-regulation。升级门槛为≥100独立簇、≥3属、≥30 held-out cluster families。PlantCAD2/AgroNT参与局部比较，Evo2参与完整长程比较。

### B12 十字花科跨属低样本迁移（确认性）

- **任务集合**：结构边界、region、promoter/TE、NLR和表达中至少3个家族。
- **目标属**：至少3个未见或标签未见属，如Brassica、Camelina、Cardamine；实际名单在taxonomy和标签审计后冻结。
- **标签预算**：1%、5%、10%是primary学习曲线；100%只作上限，不进入primary sample-efficiency AUC。
- **split**：目标test永不进入任务训练，orthogroup和assembly cluster隔离；label-transfer与true-genus-holdout分表。
- **最低门槛**：每个目标属×任务的固定test≥500独立单位且每个主要类别≥50；三个预算使用nested train subset。
- **主指标**：1%/5%/10%主指标的macro sample-efficiency AUC。
- **基线**：PlantCAD2-M/L、AgroNT、PlantCaduceus、GPN适用任务、NT-v2、DNABERT-2、Caduceus和随机初始化。
- **意义**：回答专属预训练是否真正减少新十字花科物种的标注需求。

---

## 11. 基线重跑与统计合同

### 11.1 必跑基线层级

**植物核心**：AgroNT-1B、PlantCAD2-M、PlantCAD2-L、PlantCaduceus-l32、GPN-Brassicales。

**通用核心**：NT-v2-500M、DNABERT-2、Caduceus、HyenaDNA；Evo2-7B用于zero-shot和长程能力，Evo2-1B-base用于8K可执行对照。

**任务专家**：AUGUSTUS/Helixer/GeMoMa、SpliceAI式模型、NLR-Annotator、BLAST/MMseqs2+synteny、phyloP/phastCons、SV/pangenome流程、Enformer/Borzoi/3D专家。

**简单基线**：prevalence、GC/length/repeat logistic、k-mer TF-IDF、XGBoost、one-hot CNN、随机初始化本架构。

### 11.2 同等下游预算

每个可训练协议使用五个下游seed。首先冻结骨干+线性probe；其次PEFT，按可训练参数量而不是LoRA rank机械匹配，目标±10%；只有所有主要模型都能执行且数据充足时做full fine-tuning。相同最大optimizer steps、early stopping、train-only标准化和development选择。不能给本模型大head、给公共模型线性head。

取消本模型预训练token上限不等于可以忽略计算公平性。所有基础模型结果必须并列报告其公开或实测的pretraining processed tokens、FLOPs、参数量、上下文和数据域；对本模型另外保存按`scheduled_sampling_tokens`或FLOPs对齐的中间checkpoint，用于compute-matched辅助轨道。最终WSD winner用于实际系统能力轨道，但若其计算量更大，不能把优势表述成样本效率或同计算预算优势。

### 11.3 上下文公平性

每个结果表必须写实际输入长度。AgroNT约6.1 kb、PlantCAD2 8,192 bp、PlantCaduceus/GPN 512 bp、NT-v2理论约12.3 kb、Evo2可到1M。本模型专属长程任务分别报告：

1. 所有可比较模型的官方/native长度；
2. 本模型8K context-matched结果；
3. 本模型32K/64K/128K能力结果；
4. 只改变本模型上下文的消融。

短模型中心裁剪不是“模型运行失败”，但不能声称它看到了裁剪外的证据；Evo2必须作为真正长上下文对照，防止把长度优势误说成十字花科知识。

### 11.4 统计

置信区间按最高层独立生物单位cluster bootstrap，seed方差单独报告。每个bootstrap replicate中先取公共基线最大分数，再计算本模型相对`max(public)`的paired差；p值用同一单位的paired permutation/randomization test。

十个确认性家族包含11个primary hypotheses：P3和P4各一个，其余P7、B1、B2、B3、B5、B7、B8、B9、B12各一个；11个p值统一Holm校正。只有平均效应达到train-only冻结的MMED、95% CI下界>0且Holm-adjusted `p<0.05`才通过。缺失基线、seed不完整、样本不足或CI不可算都算未通过，不从分母删除。

### 11.5 Foundation model成功标准

- 公共任务不能系统退化；对PGB和PlantCAD2兼容任务，应在大多数任务上达到预注册非劣界限，并完整报告未达到项。
- 十个确认性家族至少七个通过；P3/P4结构、B1 U三角和B5 S-locus必须通过；B7/B8/B9至少两个通过。
- 必须超过随机初始化，并有结构监督、homeolog目标和128K机制一致的消融。
- 任一split泄漏、test反复查看或post-hoc更换primary endpoint都会使相关claim失效。

如果不满足，只能表述为“构建并系统评估了十字花科预训练模型”，不能改任务或重复test挽救结论。

---

## 12. 为什么这些专属任务可能让公共模型表现差

表中“缺口”是可检验机制，不是预定结论。尤其Evo 2的上下文比本模型更长；如果本模型在S-locus或SV上超过Evo2，更合理的解释应是领域语料、双向MLM和十字花科关系目标的组合，而不是长度。

| 能力缺口 | AgroNT | PlantCAD2 | NT-v2-500M | Evo2-7B | 本模型设计的针对性 |
|---|---|---|---|---|---|
| 单碱基边界/变异 | 6-mer不直接对齐单碱基 | 支持 | 6-mer | 支持 | 单碱基+boundary/frame监督 |
| >8K双侧上下文 | 约6K | 8K | 约12K | 可到1M | 最高128K双向；Evo2仍是强对照 |
| 十字花科全基因组非基因区 | 48种植物全基因组片段 | 65种被子植物，但以gene±5kb窗口为主 | 无植物 | 全生命域含植物 | Brassicaceae全核基因组、TE/intergenic分层 |
| U三角和homeolog pair | 无显式目标 | 无显式目标 | 无 | 无 | 共线pair InfoNCE+edge-disjoint训练 |
| WGT保留/分馏 | 无 | 无 | 无 | 无 | 十字花科orthogroup/block标签与专属任务 |
| S-locus/NLR/基因簇完整区域 | context不足 | context不足 | 多数不足 | 可见完整区域但不专属 | 128K+家族专属数据；必须与Evo2比较 |
| 多倍体表达偏倚 | 一般表达任务 | 一般跨物种表达 | 非植物 | 通用LM | 成对homeolog输入、专属split和DNA-only/条件榜 |
| 低样本十字花科迁移 | 植物广义先验 | 被子植物广义先验 | 无植物先验 | 广义生命先验 | 领域深度与关系监督，靠nested学习曲线检验 |

---

## 13. 从现在到论文的执行顺序

1. 冻结task registry、11个primary endpoints、独立单位、最低门槛和test身份hash。
2. 重新解析广义植物池的taxonomy、来源、版本和checksum，得到新的Brassicaceae候选清单。
3. Assembly/contig QC、exact/RC exact、ANI近重复和污染审计。
4. 构建orthogroup、synteny、homeolog、LD、haplotype和SV不可拆分组件。
5. 根据下游test hash先做131,071 bp halo排除，再冻结预训练90/5/5 split。
6. 构建sequence、structure、TE和pair store；生成真实六长度容量与混杂报告。
7. 冻结各pool的coverage-cycle排列、跨cycle受控复用/deficit规则、长期context比例和首轮unique容量；表4.6只作10,000步参考记账。
8. 完成331,661,083参数实现、单元测试、DDP全局分母和原子checkpoint。
9. q05完成全库CPU Gate和真实bundle只读smoke；用户授权后，launcher完成三卡空闲预检和step 1前单次真实128K最坏几何GPU acceptance。
10. 启动无预定总token/step上限的唯一正式run；只用冻结development规则触发WSD decay，并按fixed development MLM NLL选winner。
11. Winner、head、seed和baseline revision全部冻结后，执行公共任务和五seed下游。
12. 一次读取sealed pretraining test和下游sealed test，做cluster bootstrap、permutation和Holm校正。
13. 发布一个最终checkpoint、数据/代码receipts、完整失败项和可复现论文图表。

---

## 14. 主要风险和停止条件

- **数据暴露风险**：Brassicaceae unique容量可能有限，跨cycle训练可能让少数assembly或稀有locus重复过多。处理：cycle内无放回、首轮优先、pool最多领先一个cycle、rare-pool重复上限、unique/scheduled/processed分账和逐来源暴露报告；不把exposure-equivalent写成严格epoch。
- **128K显存风险**：完整331M模型可能不能在40GB上满足门禁。处理：按冻结顺序优化；仍失败则BLOCKED，不改名为同一模型。
- **标签风险**：S-locus、品质、抗病或SV影响的DIRECT标签可能不足。处理：在预训练前判定infeasible，保留探索性但不删确认性分母。
- **PlantCAD2竞争风险**：PlantCAD2-M规模相近且植物通用任务很强。处理：公共任务以非劣为目标，专属任务必须包含其M/L版本，不回避。
- **GPN近域风险**：GPN在Arabidopsis/Brassicales变异上可能非常强。处理：P7必须保留GPN，不能只和通用模型比。
- **Evo2规模风险**：Evo2可能凭1M上下文和9T级训练赢得长程任务。处理：真实报告；本项目只在领域专属性和效率上形成主张。
- **预训练seed风险**：只有一条完整lineage。处理：披露，不把下游五seed包装成预训练稳定性。
- **因果归因风险**：架构、语料、目标同时变化。处理：依靠内部消融解释机制；没有广义植物同架构控制时不做语料单因素因果结论。

---

## 15. 交付物与验收清单

### 数据完成时必须出现

- 新的Brassicaceae assembly manifest及真实物种/属/倍性统计；
- 六长度真实候选、QC后、首轮unique容量，以及按cycle/context/region/taxon/source累计的realized窗口、scheduled tokens和processed tokens；
- train/development/test/保留acceptance各自hash与近重复交集为0的receipt；runtime GPU acceptance不是第五个split；
- task exposure matrix与131,071 bp halo审计；
- 自包含数据bundle及离线回读验证。

### 模型完成时必须出现

- 参数总数331,661,083的逐tensor清单；
- 六长度forward/backward、RC坐标、远端依赖和DDP归一化测试；
- 3×A100 40GB真实显存、tokens/s、step time和ETA；
- step 1前128K GPU acceptance回执，以及正式run达到500-step边界后的per-rank RNG exact-resume回执；
- winner选择和一次性test访问记录。

### 下游完成时必须出现

- 每个任务的来源、accession、样本流转、split单位和最终n；
- AgroNT、PlantCAD2-M/L、NT-v2、Evo2以及任务适用的PlantCaduceus/GPN真实重跑；
- 五seed、最高层cluster CI、Holm校正、失败任务和完整source data；
- 公共任务与专属任务分表，内部消融另表。

---

## 16. 关键来源

1. AgroNT：Mendoza-Revilla et al., *A foundational large language model for edible plant genomes*, Communications Biology 2024, https://doi.org/10.1038/s42003-024-06465-2 。
2. AgroNT权重与PGB：[model](https://huggingface.co/InstaDeepAI/agro-nucleotide-transformer-1b)，[dataset](https://huggingface.co/datasets/InstaDeepAI/plant-genomic-benchmark)。
3. PlantCAD2：Zhai et al., *PlantCAD2: a DNA foundation model for interpreting genomes across flowering plants*, bioRxiv 2025, https://doi.org/10.1101/2025.08.27.672609 。
4. PlantCAD2公开集合：https://huggingface.co/collections/kuleshov-group/plantcad2-67e437e241a382671371a572 。
5. PlantCaduceus：Zhai et al., PNAS 2025, https://doi.org/10.1073/pnas.2421738122 。
6. GPN：Benegas et al., PNAS 2023, https://doi.org/10.1073/pnas.2311219120 。
7. Nucleotide Transformer：Dalla-Torre et al., Nature Methods 2025, https://doi.org/10.1038/s41592-024-02523-z 。
8. NT-v2-500M权重：https://huggingface.co/InstaDeepAI/nucleotide-transformer-v2-500m-multi-species 。
9. Evo 2：Brixi et al., Nature 2026, https://doi.org/10.1038/s41586-026-10176-5 ；代码与模型：https://github.com/ArcInstitute/evo2 。
10. Caduceus：Schiff et al., ICML 2024, https://proceedings.mlr.press/v235/schiff24a.html 。
11. DNA foundation model公平评测：Nature Communications 2025, https://doi.org/10.1038/s41467-025-65823-8 。
12. DNALONGBENCH：Nature Communications 2025, https://doi.org/10.1038/s41467-025-65077-4 。
13. SegmentNT：Nature Methods 2025, https://doi.org/10.1038/s41592-025-02881-2 。

---

## 17. 白话总结

这个项目的目标不是做一个比Evo 2更大的模型，也不是复制AgroNT或PlantCAD2。我们的模型只有约3.32亿训练参数，unique语料域限定在十字花科；最终processed-token规模不预先封顶，而由冻结development收敛规则决定。它真正应该赢的地方，是把十字花科内部最重要、最复杂的关系学深：二倍体与异源多倍体的homeolog、U三角亚基因组、WGT后的保留与分馏、S-locus、NLR和抗病、硫代葡萄糖苷与油用品质、PAV/SV/TE以及跨属少样本迁移。

为了让这个结论可信，公共模型已有的任务一个也不能故意躲开：AgroNT的PGB要做，PlantCAD2的zero-shot和跨物种任务要做，NT-v2要作为无植物预训练的通用对照，Evo 2要作为真正长上下文对照，GPN要作为Brassicales变异强基线。一般任务上争取媲美，专属任务上用严格未见orthogroup、未见haplotype clan、未见cultivar和未见属证明优势。如果最后没有超过，就如实收缩主张；如果超过，才有资格说这是一个真正有用的十字花科基因组基础模型。
