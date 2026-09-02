# BrassicaceaeGenomeFM 最终下游任务体系

## 0. 任务体系的作用与当前状态

这套任务不是附属展示，而是论文能否成立的证据主体。通用任务证明模型不是只会记十字花科物种；十字花科专属任务证明专门预训练确实解决了其他基因组文章没有系统解决的问题。

当前结果状态仍为`DESIGNED / NOT EXECUTED`：尚无正式模型预测、分数或排行榜。数据层面已有P1/P3/P4/P8/P10/P13六项任务的12个release冻结，共521,204个样本；其余26项任务仍未冻结数据。本文不能被引用为“评测已完成”。

论文的中心命题预注册为：

> 一个以单碱基、双向超长序列建模为骨干，并显式学习十字花科基因结构与多倍体homeolog关系的模型，应在通用植物基因组任务上保持竞争力，同时在U三角、多倍体亚基因组、S-locus、抗病基因簇、品质/开花调控和泛基因组变异任务上获得可重复的专属优势。

只有在严格split、五个下游训练seed、强公共模型真实重跑和同架构随机初始化对照都完成后，才允许形成这项主张；这不代表完成了五条独立基础预训练lineage。

## 1. 证据层级

### 1.1 主榜：DNA-only

主榜的模型输入只能是DNA序列以及由任务定义自然产生的padding mask。禁止把物种名、assembly ID、染色体坐标、基因名、亚基因组标签、表达量或环境变量作为本模型隐藏输入。

主榜包括：

- 通用序列分类和单碱基结构；
- 长程DNA到表达/调控；
- DNA-only变异效应；
- 十字花科多倍体、专属基因簇和泛基因组任务。

### 1.2 扩展榜：DNA + 条件/多组学

组织、处理、环境、染色质、表达或群体特征作为输入时，必须单列扩展榜。该榜可借鉴 GET、Corgi、Enformer/Borzoi 和 AlphaGenome 的条件化设计，但不能与DNA-only模型直接比较绝对值。

### 1.3 机制证据

内部消融只回答模型为何有效：结构监督、homeolog对比目标、128K、RC一致性和数据平衡。内部变体不能替代公共强基线。若未额外训练同架构、同token、同QC的广义植物语料控制模型，不能把本模型与AgroNT/PlantCAD2/PlantCaduceus的差异解释成“十字花科语料的纯因果效应”；只能主张整个专属训练系统的实用优势。

## 2. 公共论文任务覆盖

本项目尽量覆盖现有主要基因组模型论文已经建立的任务，同时只采用合法可比的输入合同。

| 任务家族 | 对应工作 | 本项目正式任务 |
|---|---|---|
| promoter/enhancer/TF/histone分类 | DNABERT、DNABERT-2/GUE、Nucleotide Transformer | 植物和十字花科重新构建的匹配分类集 |
| 植物调控注释、启止子强度、组织表达 | AgroNT/PGB，[10.1038/s42003-024-06465-2](https://doi.org/10.1038/s42003-024-06465-2) | PGB兼容任务真实重跑；另建Brassica外测 |
| 被子植物zero-shot与跨物种功能 | PlantCAD2，[10.1101/2025.08.27.672609](https://doi.org/10.1101/2025.08.27.672609) | 复现其12项zero-shot和7项微调范式；增加Brassicaceae整属/orthogroup严格留出 |
| 翻译启止、剪接供受体 | PlantCaduceus，[10.1073/pnas.2421738122](https://doi.org/10.1073/pnas.2421738122) | Arabidopsis→Brassica跨属、跨倍性迁移 |
| 单碱基多标签注释 | SegmentNT，[10.1038/s41592-025-02881-2](https://doi.org/10.1038/s41592-025-02881-2) | 植物多转录本、TE和frame联合分割 |
| gene expression/RNA coverage | Enformer、Borzoi、GET | 十字花科DNA-only表达与条件化扩展榜 |
| enhancer–gene、eQTL、3D结构、TSS长程任务 | DNALONGBENCH，[10.1038/s41467-025-65077-4](https://doi.org/10.1038/s41467-025-65077-4) | 兼容公共任务；有数据时建立植物同构任务 |
| 零样本变异效应 | GPN、GPN-MSA、PlantCAD2、PlantCaduceus、AlphaGenome、Evo 2 | Arabidopsis/Brassica MAF、GWAS/QTL和功能变异 |
| 统一DNA-FM公平评测 | Nature Communications benchmark，[10.1038/s41467-025-65823-8](https://doi.org/10.1038/s41467-025-65823-8) | mean pooling、head和split统一重跑 |
| 3D基因组 | Akita、Orca、AlphaGenome | 只在有高质量植物Hi-C标签时进入主结果 |
| 生成和设计 | DeepSTARR、OmniReg-GPT、Evo 2 | 只作未来扩展；首篇不以未验证生成序列为主张 |

## 3. 统一评测合同

### 3.1 数据冻结顺序

1. 在预训练release之前冻结task registry、每项primary endpoint、最高层独立单位、最低样本/类别门槛和clean-inductive/label-transfer轨道；
2. 先用metadata与序列/关系图定义不可拆分生物单位；任务split求解器只可使用单位级标签分层来保证各类最低支持，不能使用模型embedding、预测或效应大小择优，并冻结身份hash；标签值不提供给预训练构建器；
3. 对clean-inductive轨道生成pretraining exclusion hash，使对应assembly/区域/orthogroup/haplotype及近重复组件不能进入预训练train、development或acceptance pool；区域向两侧扩展131,071 bp禁入halo，拒绝任何与halo相交的预训练窗口；
4. 只在train拟合标准化、负例抽样、类别权重、阈值和任何残差基线；
5. development用于head、超参数和seed/checkpoint选择；
6. winner、checkpoint、head、primary endpoint和seed矩阵冻结后，sealed test只读取一次；
7. 任何失败的正式test运行也消耗该次claim，禁止反复试到满意。

某任务若在只读metadata审计中达不到最低独立单位、阳性数、属/品种覆盖或直接标签质量，必须在预训练前标记`INFEASIBLE_FOR_CONFIRMATORY`，而不是训练后看test不好再删除。它可保留为探索任务，但不能改变十个确认性任务的分母。

### 3.2 禁止随机窗口split

不同任务使用不同最高层独立单位：

| 任务 | 最低split单位 |
|---|---|
| 通用窗口分类 | assembly similarity cluster；必要时整物种/整属留出 |
| gene结构 | orthogroup + assembly cluster |
| 表达 | accession/cultivar × study × tissue或condition |
| homeolog/亚基因组 | orthogroup + cultivar，不允许同一homeolog组跨split |
| S-locus | S-haplotype clan + accession cluster |
| 抗病 | NLR/基因orthogroup + pathotype/study |
| GWAS/QTL变异 | 染色体区段 + population/study；LD block不跨split |
| SV/PAV/TE | SV cluster + accession/pangenome graph component |
| 3D/远端调控 | 染色体或大片段block + cell/tissue/study |

同一基因的重叠窗口、反向互补、同一accession多版本、近重复assembly、homeolog对和高相似区段不能跨split。

跨物种结果必须分成两个协议：目标物种序列参加过无标签预训练但目标标签未见，称为“label transfer”；目标整物种或整属完全未参加预训练，才称为“true species/genus holdout”。公共模型预训练语料无法完全审计时，标记潜在历史暴露，不把它误写为严格零样本。

每项正式结果旁必须附 `pretraining_exposure_matrix`：本模型和每个公共模型分别标记exact assembly、同物种、同属、同科、窗口近重复、orthogroup/haplotype/LD block及监督标签暴露状态。公共模型状态不明写`UNKNOWN`，不能写`NO`。clean-inductive和label-transfer分表报告，不计算一个混合平均数。

### 3.3 Hard negative规则

负例必须来自明确callable universe，而不是把“未标注”全部当负例：

- 长度、GC、N、repeat比例和染色体背景匹配；
- gene-family任务在同家族内选难负例；
- variant任务在相同MAF、LD block、功能区域和测序callability下匹配；
- promoter/enhancer在相同距TSS和开放染色质背景下匹配；
- resistance任务用未证实同源NLR和同区域非抗性haplotype作hard negative；
- 未测量、未知、无法映射、标签冲突分别编码，不能合并为0。

### 3.4 训练协议

每个下游可训练方法使用5个正式seed。所有模型使用同一train/development/test、相同最大epoch/optimizer-step预算、相同early-stopping指标和同等head容量。这里的五seed是linear head、adapter或full fine-tuning seed；如果没有五条独立完整基础预训练lineage，就不能把它报告为foundation-pretraining seed稳定性。

本模型预训练不设累计token上限，因此必须额外公开最终winner及预先保存的compute-matched checkpoints对应的`scheduled_sampling_tokens`、`processed_forward_tokens`、FLOPs、参数量和上下文。最终WSD winner进入native-capability主轨；与公共模型可获得训练规模对齐的checkpoint进入compute-matched辅助轨。若本模型使用更多计算，不能把性能优势写成同计算预算优势或更高样本效率。

依次报告：

1. frozen encoder + linear head；
2. 同预算parameter-efficient tuning；
3. 数据量足够且所有模型可执行时的full fine-tuning。

公共模型如果上下文不足，按其官方最大长度中心裁剪，并在结果表标记实际可见长度；不能拼接多个独立短窗口后声称等价128K。API-only、多组学输入或无法获得权重的模型单列，不把缺失值当失败。

上下文比较固定为三条轨道：官方任务长度复现；同一任务/split/head但逐模型报告实际可见长度；原生能力轨道。后者允许本模型使用128K、Evo 2使用其可执行长上下文，短模型中心裁剪。另给本模型8K context-matched结果以及32K/64K/128K消融。短模型看不到远端证据不叫“运行失败”，但也不能声称获得完整长程输入；Evo 2必须进入真正长程任务，防止把纯长度优势误写成十字花科知识。

本模型在预训练中使用结构和homeolog辅助标签，因此相关任务不能包装成“纯零样本”。正式比较必须同时提供self-supervised-only消融，并让公共骨干在完全相同的train标签和head预算上微调；所有辅助标签只来自train独立单位，development/test标签不得参与预训练。

### 3.5 统计和报告

- binary：AUPRC为主，AUROC、MCC、balanced accuracy为辅；
- multiclass：macro-F1为主，balanced accuracy和per-class recall为辅；
- segmentation：per-class base AUPRC/F1、boundary F1（精确、±1 bp、±3 bp）和segment IoU；
- regression：Spearman为主，R²、MAE为辅；
- retrieval：MRR、Recall@1/5/10；
- variant ranking：AUPRC、top-1% recall、matched-pair accuracy、与MAF/实验效应的Spearman；
- 3D/profile：按染色体分层的Pearson/Spearman和距离分层相关。

置信区间以最高层独立生物单位做cluster bootstrap。seed间方差与生物单位CI分开报告；不能把seed×样本当额外独立样本。最小有意义效应（MMED）在train-only pilot和功效分析后、查看sealed test前冻结。

“超过最强公共模型”不允许在test后挑一个容易赢的比较对象。每项任务的可执行公共基线集合先冻结；每个cluster-bootstrap replicate都以该replicate中公共基线的最大分数作为competitor，计算本模型相对`max(public baselines)`的差。效应CI使用cluster bootstrap，单侧p-value使用同一最高层独立单位上的paired cluster permutation/randomization test。十个确认性家族实际包含11个primary hypotheses（P3和P4各一个，其余各一个），对这11个primary p-value统一做Holm family-wise校正；secondary endpoints另表报告，不参与资格判定。

单个primary hypothesis只有同时满足“平均效应不低于冻结MMED、95% cluster-bootstrap CI下界大于0、Holm-adjusted `p<0.05`”才记为通过；缺失基线、未完成seed、CI无法计算或样本量低于冻结门槛均按未通过，而不是从分母移除。

十个确认性任务家族的primary endpoint固定如下；表内指标决定“通过/未通过”，同一任务的其他指标只能解释，不能事后替换primary endpoint救回结论：

| 确认性家族 | Primary endpoint | 通过规则 |
|---|---|---|
| P3/P4结构 | P3四类边界macro-AUPRC与P4九类region macro-AUPRC | 两项都超过最强可执行公共模型并达到各自MMED才算该家族通过 |
| P7变异 | matched callable set上的zero-shot ref/alt pseudo-log-likelihood AUPRC | 无训练head；生物单位bootstrap差达到MMED，微调分数仅作secondary |
| B1 U三角 | 未见orthogroup上的MRR | 同上，并超过BLAST/MMseqs2+synteny规则 |
| B2表达偏倚 | homeolog pairwise accuracy | 同上，并超过train-only表达/序列简单基线 |
| B3保留/分馏 | macro-F1 | 三个retention类别均有独立test支持 |
| B5 S-locus | 未见haplotype clan的retrieval MRR | 同上，并超过haplotype/BLAST规则 |
| B7品质 | matched causal-variant AUPRC | direct标签为主；proxy标签只能作敏感性分析 |
| B8抗病 | pathotype/study-held-out AUPRC | 同上，并超过NLR专家规则 |
| B9 PAV/SV/TE | event-level regulatory/phenotypic impact macro-F1 | event type AUPRC和breakpoint F1为secondary，不得替代impact失败 |
| B12低样本迁移 | 1%/5%/10%标签量学习曲线的macro sample-efficiency AUC | 预训练见过与完全未见目标属分别判定 |

MMED、最低独立单位数、bootstrap层级和Holm family在task registry中冻结并hash绑定；sealed test之前不得改表。

### 3.6 确认性任务最低数据门槛

当前已有六项任务的12个下游数据release，但完整32项任务尚未闭环。下表仍是进入确认性主分析的预注册下限，不是现有release的实际样本数；已冻结release也必须逐项满足相应独立单位和标签质量要求后，才能进入确认性分析。任何任务低于下限，在正式test前标记`INFEASIBLE_FOR_CONFIRMATORY`；不能用更多重叠碱基或proxy标签替代独立生物单位。

| 家族 | 最低直接/强标签与独立覆盖 |
|---|---|
| P3 | 每类test阳性≥10,000；≥3个held-out属、500个未见orthogroup、6个assembly clusters |
| P4 | ≥6个held-out assembly clusters、2,000个未见orthogroups；常见region每类≥1M callable test bases |
| P7 | ≥200个DIRECT/STRONG positives、≥400匹配负例、≥30 LD blocks、≥3 studies |
| B1 | U三角六物种全覆盖；test≥1,000 queries、≥300未见orthogroups、每个A/B/C来源类≥200 queries |
| B2 | ≥1,500可靠homeolog pairs、≥3 studies、≥3 tissues/conditions；sealed test≥300 pairs且每类≥100 |
| B3 | ≥900 orthogroups、每类≥100独立test units、≥3 genera |
| B5 | ≥100 accessions、≥30 haplotype clans；test≥10未见clans和≥500 compatibility pairs |
| B7 | ≥100 DIRECT/STRONG causal positives、≥300匹配负例、≥3 studies、≥3 trait families |
| B8 | ≥100阳性locus-haplotype-pathotype units、≥30独立test loci、≥3 pathotypes、≥3 studies |
| B9 | ≥300个有DIRECT/STRONG impact标签的events、主要类别各≥50、≥3 pangenome/study来源 |
| B12 | ≥3目标属×≥3任务家族；每个属×任务固定test≥500独立单位且每个主要类别≥50 |

其他binary确认性任务至少100阳性、100匹配负例和30个最高层独立单位；multiclass至少每类50且总数≥300；regression至少300样本和30个最高层clusters；retrieval至少500 queries、100未见families且每query≥20 candidates。精确功效与MMED仍由train-only pilot在查看sealed test前冻结，但不得低于本表。

## 4. 公共与简单基线

### 4.1 必跑DNA foundation models

| 模型家族 | 主要角色 | 公平性说明 |
|---|---|---|
| DNABERT、DNABERT-2-117M | 短上下文Transformer/GUE基线 | 同时报告官方pooling和统一mean pooling |
| Nucleotide Transformer 50M/500M或可执行近似规模 | 多物种Transformer | 不因2.5B显存不可行而把整家族删除 |
| HyenaDNA | 单碱基长序列 | 使用公开最长兼容checkpoint |
| Caduceus-PH/PS | 双向/RC长序列 | 是架构最接近的关键基线 |
| GROVER | BPE人类DNA模型 | base级任务需明确token对齐限制 |
| AgroNT-1B | 公开植物专用强基线 | PGB和十字花科任务必须有 |
| PlantCAD2-M/L | 当前最关键单碱基植物基线 | 约311M M版作近参数匹配、约694M L版作强植物上界；锁定公开revision并按运行时参数receipt，不能只引用预印本分数 |
| PlantCaduceus | 公开植物单碱基强基线 | 植物跨物种和变异任务必须有 |
| GPN/GPN-MSA | 零样本变异效应 | GPN-MSA属于有额外比对输入的扩展对照 |
| Evo/Evo 2 | 超长生成式DNA模型 | 权重和硬件可执行时真实重跑；否则报告可执行边界 |
| AlphaGenome | 统一序列到功能 | 适配物种和API允许时作专家模型，不与纯自监督等同 |
| Enformer/Borzoi | 表达/调控专家 | 只参加其原生输出可比任务 |

模型版本、权重hash、tokenizer、remote code commit和许可元数据在执行时冻结。论文中的公开分数只用于核对趋势，正式表格全部来自本项目真实重跑。

### 4.2 必跑非预训练基线

- majority/prevalence和随机排序；
- GC/长度/repeat logistic regression；
- k-mer TF-IDF + logistic/XGBoost；
- one-hot浅层CNN；
- DeepSEA/BPNet式任务CNN；
- 同架构 `BrassiCaduceus-330M` 随机初始化；
- 同参数预算单向Mamba；
- gene annotation任务的 AUGUSTUS/Helixer/GeMoMa 等专家工具；
- orthology/homeology任务的 BLAST/MMseqs2 + synteny规则；
- variant任务的 phyloP/phastCons、SIFT/蛋白模型或任务对应公开专家分数；
- 表达任务的promoter k-mer、gene length/GC和公开sequence-to-function专家模型。

## 5. 通用与植物公共任务

### P1. 通用调控序列分类

- **输入**：相同长度DNA窗口；4K为主，另报模型原生长度。
- **标签**：promoter、enhancer、enhancer type、TF-binding、histone mark、开放染色质；来自GUE、NT任务和可重建植物数据。
- **split**：染色体/assembly cluster；重叠peak和同源窗口成组。
- **负例**：同GC、长度、repeat、染色质callable背景。
- **指标**：AUPRC、MCC、macro-F1。
- **目的**：证明基础表征可迁移；不作为十字花科创新主张。

### P2. Plants Genomic Benchmark兼容任务

- **输入**：按AgroNT/PGB定义的DNA窗口。
- **标签**：植物调控注释、promoter/terminator strength、组织特异表达和功能变异。
- **split**：先复现官方split，再增加按物种/属留出的严格split。
- **基线**：AgroNT、PlantCAD2-M/L、PlantCaduceus、NT、DNABERT-2、随机初始化。
- **指标**：遵循原任务并增加五seed和cluster bootstrap。
- **边界**：官方任务结果与严格split结果分列，不能混合。

### P2B. PlantCAD2兼容任务

- **公开来源**：PlantCAD2预印本及其[Hugging Face公开集合](https://huggingface.co/collections/kuleshov-group/plantcad2-67e437e241a382671371a572)。
- **zero-shot覆盖**：跨物种conservation、TIS/TTS、splice donor/acceptor motif recovery、core/non-core junction conservation和SV effect，共12项公开范式。
- **微调覆盖**：跨物种ACR、multi-species ACR、92-cell-type ACR、gene-expression on/off与回归、translation on/off与回归，共7项。
- **协议**：先按公开8,192 bp合同和数据复现，再在Brassicaceae上冻结整属、orthogroup和assembly-cluster留出；公开结果与本项目严格结果分表。
- **关键基线**：PlantCAD2-M约311M用于近参数匹配，PlantCAD2-L约694M用于最强植物上界；摘要“676M”与正文“694M”的数字差异由具体revision加载后的参数receipt处理。
- **目的**：证明本模型不是因为绕开当前最强植物任务而获胜；若公共任务退化，必须如实报告。

### P3. 翻译和剪接边界跨物种迁移

- **输入**：边界中心窗口及完整长上下文。
- **标签**：translation start/stop、splice donor/acceptor。
- **split**：Arabidopsis训练，Brassica/Camelina/Cardamine等整属或整物种外测；orthogroup不跨split；分别报告label-transfer和pretraining完全留出的true-holdout协议。
- **hard negative**：同区域、同frame、相似motif但不是真边界的位置。
- **指标**：AUPRC、MCC、精确与±1/±3 bp boundary F1。
- **基线**：PlantCAD2-M/L、PlantCaduceus、SegmentNT兼容模型、SpliceAI式专家、PWM。

### P4. 单碱基多标签基因组分割

- **输入**：4K、16K、50K/64K窗口。
- **标签**：9个region、3个CDS frame、6个边界；unknown单独mask。
- **split**：orthogroup和assembly cluster双重隔离；整物种外测。
- **指标**：per-class AUPRC/F1、segment IoU、boundary F1。
- **基线**：PlantCAD2-M/L、PlantCaduceus、SegmentNT、Helixer、AUGUSTUS、one-hot U-Net/CNN、随机初始化骨干。
- **边界**：仅在独立高质量注释上称“跨物种注释”；不能用训练注释自评。

### P5. DNA到表达和RNA覆盖

- **输入**：基因TSS中心32K/64K/128K序列；DNA-only主榜。
- **标签**：可比组织/条件下的TPM或RNA coverage，先按study内处理。
- **split**：整基因orthogroup、accession和study；同一基因不同转录本不能跨split。
- **指标**：gene-wise Spearman、R²、MAE；跨组织和跨物种分别报告。
- **基线**：promoter k-mer、Enformer、Borzoi、AgroNT、PlantCAD2-M/L、PlantCaduceus、GET/Corgi扩展榜。
- **边界**：DNA-only不能解释全部环境诱导表达；上限和不可解释方差必须报告。

### P6. 长程调控与DNALONGBENCH兼容任务

- **任务**：enhancer-target、eQTL关联、3D组织、regulatory activity、TSS信号。
- **长度**：32K、64K、128K；公共原任务可到1M时，本模型只在128K范围内参评并明确截断。
- **split**：染色体block和study；相邻重叠区域成组。
- **指标**：任务原始指标，加距离分层性能。
- **基线**：HyenaDNA、Caduceus、PlantCAD2-M/L、Evo 2、OmniReg-GPT、任务专家。
- **目的**：证明128K有实际贡献，而不只提高短序列分类。

### P7. 零样本和微调变异效应

- **输入**：reference与alternate等长窗口；计算pseudo-log-likelihood差、embedding差和微调head三种分数。
- **标签**：实验功能、已知因果、MAF、GWAS/QTL fine-mapping；标签源分层。
- **split**：LD block、染色体、population和study。
- **负例**：相同MAF、功能区、测序callability和距基因距离。
- **指标**：AUPRC、matched accuracy、top-1% recall、Spearman。
- **基线**：GPN、GPN-MSA、PlantCAD2-M/L、PlantCaduceus、AgroNT、AlphaGenome/Evo 2、phyloP/phastCons。

### P8. 单碱基表观修饰位点分类（4mC/5mC/6mA）

- **来源**：Nature Communications DNA-FM基准 [10.1038/s41467-025-65823-8](https://doi.org/10.1038/s41467-025-65823-8) 第3/4类的植物对应实例。
- **数据集**：A.thaliana 4mC、G.pickeringii 4mC、G.subterraneus 4mC（i4mC-Deep/MethSMRT来源）；拟南芥5mC（亚硫酸氢盐验证位点）；植物6mA仅在取得可靠实验证据时进入，否则标记INFEASIBLE。
- **输入**：位点中心41 bp窗口（与NC基准一致的局部信号长度）；另报4K原生长度结果。
- **split**：染色体+site cluster；同基因同源位点不跨split；负例为同GC、同二核苷酸背景的callable胞嘧啶。
- **指标**：AUPRC、MCC、macro-F1；跨物种外测（拟南芥训练→Geum外测等）。
- **基线**：k-mer/CNN、i4mC-Deep式专家、AgroNT、PlantCAD2、DNABERT-2、NT-v2。
- **目的**：证明单碱基分辨率能力（与P4互补），并直接对表NC基准。

### P9. 开放染色质区域分类

- **来源**：NC基准DNase-I Hypersensitive任务的植物对应实例。
- **数据集**：拟南芥DNase-seq峰（Zhang et al. 2012等）；Brassica ATAC-seq峰（有public数据时）。
- **输入**：峰中心1-2 kb窗口；负例为同GC、同repeat、同染色质可测背景。
- **split**：染色体block + tissue/study；同peak同源窗口成组。
- **指标**：AUPRC、MCC、macro-F1。
- **基线**：k-mer/CNN、AgroNT、PlantCAD2、DNABERT-2、NT-v2。

### P10. 多物种基因组区域分类

- **来源**：NC基准第2类（human vs worm）的植物对应实例，扩展为科内与科间两层。
- **数据集**：
  - P10a 十字花科内属/种：Arabidopsis、Brassica、Raphanus、Camelina、Capsella、Eutrema、Sinapis、Cardamine（plantDB本地构建，每物种等量窗口）；
  - P10b 十字花科 vs 外群：Solanum、Glycine、Oryza、Zea等非十字花科植物；
  - P10c U三角亚基因组A/B/C：与B1标签体系联动，但不输入任何坐标/名称特征。
- **输入**：1-4K bp随机基因组窗口，GC/重复匹配。
- **split**：整assembly/整种留出，同一近重复区域不跨split；报告label-transfer与true-holdout。
- **指标**：macro-F1、AUPRC（one-vs-rest）、准确率。
- **目的**：验证模型学到的是植物/十字花科真实特征，而不是表面GC/重复捷径；公共模型可重跑同数据。

### P11. 增强子与增强子强度

- **来源**：NC基准enhancer/enhancer_strength的植物对应实例。
- **数据集**：拟南芥STARR-seq增强子（Jores et al. 2020等）；增强子强度按STARR活性分位定义分类/回归两轨。
- **输入**：增强子中心1-4K窗口；负例来自同批次STARR低活性同GC背景。
- **split**：染色体block；同源增强子不跨split。
- **指标**：AUPRC、macro-F1（分类）；Spearman/R²（强度回归）。
- **基线**：k-mer/CNN、AgroNT、PlantCAD2、DNABERT-2、NT-v2。

### P12. TAD边界识别

- **来源**：NC基准TAD任务的植物对应实例。
- **数据集**：拟南芥Hi-C TAD边界（Liu et al. 2017等）；Brassica Hi-C有public数据时加入。
- **输入**：边界中心2.4K bp（NC同长度）与32K/64K长上下文两轨。
- **split**：染色体block；相邻边界同组。
- **指标**：AUPRC、边界F1（±N bp）；距离分层报告。
- **基线**：k-mer/CNN、insulation-score专家规则、PlantCAD2、DNABERT-2、NT-v2。
- **边界**：植物TAD数据分辨率有限，结果仅作为能力证据，不作为核心主张。

### P13. 核心启动子与启动子强度

- **来源**：NC基准promoter套件（8数据集）的植物部分 + 本地重建。
- **数据集**：
  - P13a iPro-WAEL拟南芥TATA/NonTATA启动子（NC基准HF zip直接提取）；
  - P13b 核心启动子70 bp（本地GFF构建：TSS±35，TATAWAW基序分TATA/NonTATA）；
  - P13c 启动子300 bp（本地GFF构建：TSS-250..+50，含增强子背景负例）；
  - P13d 启动子强度回归（STARR-seq/CAGE活性，有数据时）。
- **split**：orthogroup + assembly cluster；同基因不跨split。
- **指标**：AUPRC、MCC、macro-F1；强度用Spearman/R²。
- **基线**：k-mer/PWM（TATA-box）、CNN、AgroNT、PlantCAD2、DNABERT-2、NT-v2。

## 6. 十字花科专属核心任务

以下任务是论文最大亮点。主文至少要完整完成其中预注册的核心组合，而不是只挑结果好的任务。

### B1. U三角亚基因组来源与homeolog检索

- **科学问题**：模型是否学到 `B. rapa(A)`、`B. nigra(B)`、`B. oleracea(C)` 与 `B. juncea(AB)`、`B. napus(AC)`、`B. carinata(BC)` 的祖先—亚基因组关系。
- **输入**：gene body加上下游，分别使用4K/16K/64K；不输入物种名和坐标。
- **标签**：高可信共线区、orthogroup和亚基因组注释。
- **split**：整个orthogroup和cultivar成组；test包含未见cultivar及未见homeolog family。
- **hard negative**：同基因家族但非共线拷贝、相同GC/长度的异亚基因组基因。
- **任务**：diploid–polyploid检索、A/B/C来源分类、正确homeolog排序。
- **指标**：MRR、Recall@1/5/10、macro-F1。
- **基线**：BLAST/MMseqs2、synteny规则、AgroNT、PlantCAD2-M/L、PlantCaduceus、Caduceus、Evo 2、随机初始化。
- **最小证据**：在未见orthogroup上超过最强embedding模型；不能仅靠物种特异k-mer取胜。

### B2. 多倍体homeolog表达偏倚

- **科学问题**：仅从DNA能否预测同一homeolog pair在组织/条件中的相对表达优势。
- **输入**：成对的128K或可用最大上下文；主榜只用DNA，扩展榜加入组织/环境embedding。
- **标签**：经过homeolog-aware定量的表达比；低可映射基因剔除。
- **split**：homeolog group、cultivar、tissue-study三层隔离。
- **hard negative/对照**：表达无显著偏倚pair；匹配总表达和可映射性。
- **指标**：pairwise accuracy、macro-F1、Spearman、校准误差。
- **基线**：promoter k-mer、gene/TE距离特征、AgroNT、PlantCAD2-M/L、PlantCaduceus、Evo 2、随机初始化。
- **边界**：DNA-only表现不代表解释环境响应；按组织稳定偏倚和条件特异偏倚分层。

### B3. 全基因组三倍化后的保留与分馏

- **科学问题**：十字花科古老whole-genome triplication后，哪些拷贝被保留、丢失或发生功能分化。
- **输入**：祖先/现存同源基因及64K邻域；不输入现成亚基因组标签。
- **标签**：高可信syntenic block中的single/double/triple retention和fractionation状态。
- **split**：orthogroup和syntenic block；相邻block不能跨split。
- **hard negative**：非共线家族扩张和TE介导复制。
- **指标**：macro-F1、per-class recall、校准；跨属迁移。
- **基线**：基因长度/表达/TE距离logistic、synteny统计模型、AgroNT、PlantCAD2-M/L、PlantCaduceus、GPN、Evo 2。
- **创新点**：把深层基因组表征与十字花科特有多倍体进化联系起来。

### B4. Homeologous exchange与gene conversion识别

- **科学问题**：长序列表征能否识别异源多倍体中的homeologous exchange、局部基因转换或亚基因组替换。
- **输入**：候选断点两侧32K/64K/128K序列，以及成对祖先参考窗口。
- **标签**：泛基因组/高质量比对和独立结构变异证据共同支持的事件。
- **split**：cultivar、事件cluster和染色体block。
- **hard negative**：普通同源高相似区、组装gap附近、非交换SV。
- **指标**：event-level AUPRC、breakpoint F1、来源分类macro-F1。
- **基线**：序列比对/coverage规则、SV专家流程、Caduceus、PlantCAD2-M/L、PlantCaduceus、Evo 2。
- **边界**：这是候选识别，不替代细胞遗传或长读长实验验证。

### B5. S-locus自交不亲和单倍型与功能

- **科学问题**：模型能否在高度多态、长程连锁的S-locus中识别决定花粉/柱头特异性的序列，并迁移到未见haplotype。
- **输入**：SRK/SCR及完整S-locus邻域，最高128K。
- **标签**：已核验S-haplotype、dominance class、兼容/不兼容杂交结果；可利用正式公开的Brassica A genome群体资源，例如 Nature Genetics 2026 [10.1038/s41588-026-02626-7](https://doi.org/10.1038/s41588-026-02626-7)。
- **split**：haplotype clan和accession cluster，近等位序列不跨split。
- **hard negative**：同家族受体激酶/小肽、S-locus邻近但非决定元件。
- **指标**：haplotype retrieval MRR、功能分类macro-F1、compatibility AUPRC。
- **基线**：BLAST/haplotype规则、k-mer、AgroNT、PlantCAD2-M/L、PlantCaduceus、GPN、Evo 2。
- **创新点**：这是十字花科生殖系统的家族专属长区间任务。

### B6. 春化、开花和生态适应等位变异

- **目标基因/网络**：FLC、FRI、FT、SOC1、VIN3及十字花科扩增拷贝，但标签不局限于已知基因。
- **输入**：变异前后64K/128K序列；DNA-only主榜，环境变量扩展榜。
- **标签**：多环境flowering time、vernalization response、已验证因果等位变异和fine-mapped loci。
- **split**：accession relatedness cluster、study和环境；同一主效haplotype不跨split。
- **hard negative**：同LD block、相同MAF的非因果变异。
- **指标**：variant AUPRC、top-k causal recall、表达/表型Spearman。
- **基线**：GWAS P值/LD、phyloP、GPN、AgroNT、PlantCAD2-M/L、PlantCaduceus、Evo 2、随机初始化。
- **边界**：模型排序不能替代田间因果验证；study间异质性单独报告。

### B7. 硫代葡萄糖苷与油用品质

- **科学问题**：是否能识别十字花科特有 glucosinolate 通路和油菜籽油酸、芥酸、蛋白含量等品质相关调控变异。
- **输入**：候选基因/变异周围4K–128K序列；主榜DNA-only。
- **标签**：功能验证、代谢物QTL/GWAS、稳定haplotype效应；direct与proxy分层。
- **split**：gene family、LD block、cultivar和study。
- **hard negative**：同通路非因果同源拷贝、同LD block匹配变异。
- **指标**：AUPRC、top-1% recall、效应方向accuracy、代谢量Spearman。
- **基线**：通路/注释规则、GWAS统计、GPN、AgroNT、PlantCAD2-M/L、PlantCaduceus、Evo 2。
- **创新点**：将十字花科特色代谢与基础模型证据直接连接。

### B8. 抗病NLR簇与clubroot/blackleg抗性

- **科学问题**：模型是否能在复杂NLR簇、PAV和TE富集区识别抗病基因及功能变异。
- **输入**：NLR gene加最长128K邻域、reference/alternate或presence/absence序列。
- **标签**：独立病原接种、图位克隆/功能验证、pathotype-specific resistance；预测性QTL单列proxy。
- **split**：NLR orthogroup、resistance locus、pathotype和study。
- **hard negative**：同簇未证实NLR、失活拷贝、相同结构域非抗性基因。
- **指标**：AUPRC、macro-F1、跨pathotype/物种transfer、候选top-k recall。
- **基线**：NLR-Annotator/结构域规则、BLAST、AgroNT、PlantCAD2-M/L、PlantCaduceus、GPN、Evo 2、随机初始化。
- **证据边界**：候选排序不是“发现新抗病基因”，除非有独立实验或严格外部队列。

### B9. 泛基因组PAV、SV与TE调控效应

- **输入**：reference/alternate断点两侧、插入序列和最长128K邻域。
- **标签**：高质量pangenome graph支持的PAV/SV/TE事件；表达和表型效应另作标签层。
- **split**：SV cluster、accession、graph component和染色体block。
- **hard negative**：组装gap、低可比对区、相同repeat家族但无效应事件。
- **任务**：事件类型、断点、gene/regulatory impact和core/dispensable状态。
- **指标**：event AUPRC、breakpoint F1、impact macro-F1、效应Spearman。
- **基线**：SV/TE专家注释、序列比对特征、HyenaDNA、Caduceus、PlantCAD2-M/L、PlantCaduceus、Evo 2。
- **创新点**：检验超长上下文是否真正利用TE和结构背景。

### B10. 驯化、改良与生态适应变异优先级

- **输入**：候选SNP/indel及64K/128K上下文。
- **标签**：选择扫描、GWAS/fine-mapping、功能验证和群体频率分层；选择扫描单独视为proxy。
- **split**：population、LD block、trait study和chromosome。
- **hard negative**：相同MAF、LD、距基因距离和callability的背景变异。
- **指标**：AUPRC、top-k causal recall、matched accuracy、跨作物迁移。
- **基线**：选择统计量、GWAS后验、phyloP、GPN/GPN-MSA、AgroNT、PlantCAD2-M/L、PlantCaduceus、Evo 2。
- **边界**：不能用同一群体的频率既做预训练标签又做sealed test。

### B11. 十字花科基因簇边界与长程协同调控

- **对象**：glucosinolate、NLR、次生代谢及串联复制基因簇。
- **输入**：完整32K–128K区域。
- **标签**：保守共线块、共表达模块、实验调控元件和结构边界。
- **split**：整个gene cluster family；相似簇不跨split。
- **hard negative**：相同基因密度/TE比例但无共功能的串联区域。
- **任务**：cluster boundary分割、成员功能分类、pair co-regulation预测。
- **指标**：boundary F1、AUPRC、pair ranking MRR。
- **基线**：基因距离/共表达规则、CNN、Caduceus、AgroNT、PlantCAD2-M/L、PlantCaduceus、Evo 2。

### B12. 十字花科跨属低样本迁移

- **问题**：Arabidopsis等注释丰富物种上的少量标签能否迁移到Brassica、Camelina、Cardamine等目标属/物种，并区分标签未见与预训练完全未见。
- **任务集合**：splice/start-stop、gene structure、promoter、TE、NLR和表达。
- **协议**：每个目标物种按1%、5%、10%、100%标签量建立学习曲线；预训练骨干和随机初始化使用同样标签。
- **split**：目标物种test永不进入源物种任务训练且orthogroup隔离；主表同时区分“预训练见过目标无标签序列”和“目标整属未参加预训练”两种协议。
- **指标**：各任务主指标、sample-efficiency AUC和达到固定性能所需标签量。
- **基线**：AgroNT、PlantCAD2-M/L、PlantCaduceus、NT、DNABERT-2、Caduceus、Evo 2。
- **最小证据**：优势必须在多个目标属和至少三种标签预算下稳定；只有整属未参加预训练时才使用“未见属”措辞，不能只在Arabidopsis随机split上提高。

## 7. 多组学扩展任务

以下任务不进入DNA-only主榜：

- DNA + tissue/condition预测表达；
- DNA + ATAC预测组织特异调控；
- DNA + environment预测开花、胁迫和品质；
- DNA + pangenome graph path建模PAV/SV；
- DNA + Hi-C预测亚基因组三维互作；
- DNA + methylation/TE状态分析亚基因组表达偏倚。

比较对象应包括GET、Corgi、Enformer/Borzoi或任务专家；必须同时给DNA-only增量，说明额外模态贡献。

## 8. 主文结果冻结规则

### 8.1 核心任务组合

主文确认性组合预注册为：

1. P3/P4：跨物种单碱基结构；
2. P7：植物变异效应；
3. B1：U三角homeolog/亚基因组；
4. B2：多倍体homeolog表达偏倚；
5. B3：全基因组三倍化后的保留与分馏；
6. B5：S-locus；
7. B7：硫代葡萄糖苷/油用品质；
8. B8：抗病NLR/clubroot；
9. B9：PAV/SV/TE；
10. B12：跨属低样本迁移。

某项因缺少可信直接标签无法执行时，必须在结果中报告“未完成及原因”，不能从大量候选任务中事后只选显著项。

### 8.2 Foundation model资格

最终模型只有同时满足以下条件才使用“有效十字花科foundation model”主张：

- 通用/植物公共任务不发生系统性退化；
- 十个预注册确认性任务家族中至少七个超过最强可执行公共植物模型并达到MMED；其中P3/P4结构家族、B1 U三角和B5 S-locus为必过，B7/B8/B9中至少两个通过；
- 超过同架构随机初始化，且效应达到任务冻结MMED；
- 所有可训练协议五个下游seed方向一致；确定性zero-shot任务不伪造seed重复；最高层生物单位bootstrap CI和Holm校正通过；
- 去掉结构监督、homeolog目标或长上下文后出现与机制一致的退化；
- 没有跨split近重复、orthogroup、LD block或accession泄漏。

未达到时应收缩主张为“构建并系统评估了一个十字花科预训练模型”，不能通过改任务、改seed或重复查看test挽救结论。

## 9. 论文图表规划

- **Figure 1**：数据谱系、去重/cluster split、统一多长度训练和模型结构；
- **Figure 2**：公共植物/基因组任务公平重跑；
- **Figure 3**：单碱基结构与跨属低样本迁移；
- **Figure 4**：U三角homeolog、亚基因组和多倍体专属证据；
- **Figure 5**：S-locus、抗病、品质和开花代表性任务；
- **Figure 6**：PAV/SV/TE与128K长程机制；
- **Extended Data**：全部seed、完整基线、消融、split泄漏审计、RC一致性、context/属/assembly平衡和失败任务；
- **Source Data**：每个独立生物单位的预测、标签、split、seed和模型版本，不只给汇总均值。

图表必须同时说明：任务输入、独立单位、split、横纵轴、指标方向、可支持结论和不能支持的结论。所有结果表只纳入真实运行产物，不提前填入占位分数或复制论文分数。

## 10. 任务执行状态与启动清单（2026-08-14 更新）

任务体系已从 26 项扩展为 **32 项**（20 核心 P1–P13 + B1–B12 结构不变 + 6 多组学扩展 X1–X6；新增 P8/P9/P10/P11/P12/P13 六个公共任务家族，对齐 Nature Communications《Benchmarking DNA foundation models for genomic and genetic tasks》10.1038/s41467-025-65823-8 的四大类 57 数据集，取其植物可执行部分并在本地重建同构任务）。

### 10.1 已就绪（数据 release 冻结后即可直接评测）

| 数据集 release | 任务 | 窗口 | 规模（每 split/类） | 来源 |
|---|---|---|---|---|
| p1_coding_intergenic_v1 | P1 | 2048 bp | 4000 正 + 4000 负 | plantDB 本地 GFF 派生 |
| p3_splice_donor_v1 | P3 | 600 bp | 3000 + 3000 | plantDB 本地 GFF 派生 |
| p3_splice_acceptor_v1 | P3 | 600 bp | 3000 + 3000 | plantDB 本地 GFF 派生 |
| p4_region_type_v1 | P4 | 400 bp | 4 类 × 2000 | plantDB 本地 GFF 派生 |
| p10a_species_v1 | P10a | 2000 bp | 4 物种 × 2000 | plantDB 本地（4 物种 × 全部 split） |
| p10b_species_v1 | P10b | 2000 bp | 2 类 × 3000 | plantDB 本地（十字花科 vs 番茄/水稻/玉米/黄瓜） |
| p13_core_promoter_v1 | P13b | 70 bp | 4000（TATA/NonTATA 按基序标注） | plantDB 本地 GFF 派生 |
| p13_promoter300_v1 | P13c | 300 bp | 3000 + 3000 | plantDB 本地 GFF 派生 |
| p8_4mc_athaliana_v1 | P8 | 41 bp | NC 基准 test 保留 | NC 基准 HF zip |
| p8_4mc_geum_pickeringii_v1 | P8 | 41 bp | NC 基准 test 保留 | NC 基准 HF zip |
| p8_4mc_geum_subterraneus_v1 | P8 | 41 bp | NC 基准 test 保留 | NC 基准 HF zip |
| p13a_iprowael_tata_nontata_v1 | P13a | 700 bp | NC 基准 test 保留 | NC 基准 HF zip（iPro-WAEL） |

以上 release 的 split 均为整 assembly 或序列级留出，经 `validate_splits` 泄漏审计（重复样本、RC 近重复、生物组跨界、坐标重叠）后冻结；每个 release 目录含 manifest.json + receipt.json + samples.jsonl，目录只读。

### 10.2 需要外部实验数据（来源已核实，待获取）

P5（表达，SRA）、P6（长程调控，PlantCAD2 数据）、P7（变异效应，gpn-brassicales 配套 VCF）、P9（DNase/ATAC，GSE53322/PlantDHS）、P11（STARR-seq，GSE144826）、P12（TAD，GSE96418）、B1–B12（逐任务论文补充材料）。详见 `DOWNSTREAM_DATA_ACQUISITION.md`。

### 10.3 公共基线模型权重

已缓存（本地 + 逐文件 sha256 回执）：AgroNT 1B、DNABERT-2 117M、NT-v2 500M multi-species、HyenaDNA medium 160K、GPN-Brassicales。PlantCAD2/PlantCaduceus 权重公开链接待核实；Evo 2 推迟到 GPU 长程阶段。

### 10.4 启动协议（等用户指定执行卡）

1. 用户指定 GPU 卡 → 在指定卡上运行编码与评测（下游 runner 的 brassi_frozen + 公共模型编码全部 GPU 化）；
2. 任何 CPU 残留步骤（数据解压、格式转换、统计）继续提交 q03；
3. 训练中的正式 checkpoint（每 500 步永久保存）与下游评测并行互不影响；
4. 下游评测顺序：先 12 个已冻结 release 的公共任务（P1/P3/P4/P8/P10/P13 家族），再补外部数据任务，最后 B 系列确认性任务。

### 10.5 与 NC 基准论文的对应关系

| NC 基准类别 | NC 数据集数 | 本项目对应 |
|---|---|---|
| 人类区域分类 | 约 25 | 不执行（非植物，超出项目边界；文档注明） |
| 多物种区域分类 | 8 | P10a/P10b 植物版 + P1 coding/intergenic |
| 人类表观分类 | 6 | P8 植物 4mC/5mC 对应版 |
| 多物种表观分类 | 6 | P8（A.thaliana + 2 Geum 4mC）+ P9（DNase，数据待获取） |
| 剪接位点 | 3 | P3 donor/acceptor |
| 启动子 | 8 | P13a（iPro-WAEL 复现）+ P13b/P13c（本地重建） |
| 增强子 | 2 | P11（STARR-seq，数据待获取） |
| 表达预测 | GTEx 人 | P5 植物对应版（数据待获取） |
| 变异效应 | 致病/因果 QTL | P7 植物对应版（数据待获取） |
| TAD | 1 | P12 植物对应版（数据待获取） |
