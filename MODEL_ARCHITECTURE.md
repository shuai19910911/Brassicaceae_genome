# BrassiCaduceus-330M 最终模型架构

## 0. 模型定位

`BrassiCaduceus-330M` 是面向十字花科核基因组的单碱基、双向、超长上下文 DNA foundation model。它使用 Caduceus 风格的双向 Mamba 状态空间块，在一个骨干中支持4K到128K上下文，并以十字花科基因结构、多倍体共线性和homeolog关系作为辅助监督。

本架构是正式目标，不存在小模型替代版。当前文档冻结模型合同，但代码、权重和训练结果尚未产生。训练时长不是架构参数：正式run不设预定累计token/step上限，每步固定调度786,432个scheduled sampling tokens，并按`TRAINING_PLAN.md`的coverage-cycle与WSD停止合同执行；取消上限不改变331M参数或128K上下文定义。

模型的专属性来自四部分：

1. 只用重新审计的 Brassicaceae 主体语料预训练；
2. 直接学习植物基因结构、CDS frame 和稀疏边界；
3. 使用 A/B/C 亚基因组、二倍体祖先和异源多倍体 homeolog 的高可信共线关系；
4. 用128K上下文覆盖基因簇、TE邻域、结构变异和远端调控，而不是只做短片段分类。

### 0.1 与PlantCAD2的定位差异

2025年公开的PlantCAD2是本模型最关键、也最接近的植物基线：[预印本](https://doi.org/10.1101/2025.08.27.672609)报告约88M/311M/694M的S/M/L系列，采用单碱基Mamba2、RC设计和8,192 bp上下文，在65种被子植物上预训练。正式比较必须同时使用约311M的M版作近参数匹配和约694M的L版作强植物上界；摘要“676M”和正文“694M”的差异由具体公开revision的运行时参数receipt解决。

本模型不把“使用Mamba/Caduceus”本身当新发明。与PlantCAD2相比，预注册差异是Brassicaceae全核基因组而非65种被子植物gene-centered ±5 kb窗口、最高128K而非8K、逐碱基结构联合目标和edge-disjoint homeolog关系目标。公共PGB/PlantCAD2兼容任务用于检验一般能力是否退化；U三角、WGT、S-locus、NLR/PAV/SV和跨属低样本任务用于检验这些差异是否产生实际价值。只有同数据公平重跑和消融支持后才能形成优势主张。

## 1. 输入、词表与坐标

### 1.1 单碱基输入

模型不采用k-mer、BPE或codon token。每个token对应一个碱基，因此单碱基标签、变异效应和边界定位不需要反解token。

模型词表固定为8：

| ID | token | 说明 | reverse-complement |
|---:|---|---|---|
| 0 | PAD | 仅用于真实补齐 | PAD |
| 1 | A | 腺嘌呤 | T |
| 2 | C | 胞嘧啶 | G |
| 3 | G | 鸟嘌呤 | C |
| 4 | T | 胸腺嘧啶 | A |
| 5 | N | 未确定碱基 | N |
| 6 | MASK | MLM遮蔽 | MASK |
| 7 | RESERVED | 保留，正式预训练不生成 | RESERVED |

底层语料使用 `A=0,C=1,G=2,T=3,N=4`。DataLoader加载后必须执行`+1`映射。任何直接把raw 0送进embedding的路径都是阻断性错误，因为会把A误当PAD。

### 1.2 长度和padding

正式上下文为4,096、8,192、16,384、32,768、65,536、131,072。训练按长度分bucket，因此主体训练不需要PAD；位于contig边缘的窗口若不能形成完整长度则不进入该bucket。下游变长任务允许PAD，但pooling、loss和结构head都必须使用attention/padding mask。

不添加绝对位置embedding。Mamba状态递推和局部卷积保留顺序信息，避免固定位置表限制长度外推。

## 2. 骨干结构

### 2.1 冻结超参数

| 项目 | 值 |
|---|---:|
| 架构 | bidirectional tied-projection Mamba，Caduceus-PH风格 |
| `d_model` | 1,024 |
| 层数 `n_layer` | 47 |
| Mamba expansion | 2 |
| `d_inner` | 2,048 |
| SSM state `d_state` | 16 |
| depthwise conv kernel `d_conv` | 4 |
| `dt_rank` | 64 |
| 双向融合 | elementwise add |
| 前/反向大矩阵 | `in_proj`和`out_proj`共享 |
| 前/反向SSM、conv和时间参数 | 独立 |
| norm | RMSNorm，`eps=1e-5` |
| residual | FP32 accumulation |
| dropout | 0 |
| embedding/head | MLM head与碱基embedding权重共享 |
| 最大正式上下文 | 131,072 bp |

### 2.2 单层计算

对第 `l` 层输入 `H_l`：

1. `X_l = RMSNorm(H_l + R_l)`；
2. 前向Mamba读取 `X_l[1...L]`，得到 `F_l`；
3. 反向Mamba读取倒序的 `X_l[L...1]`，输出后再倒回原坐标，得到 `B_l`；
4. `M_l = F_l + B_l`；
5. 将 `M_l` 送入下一层，同时保留残差分支。

前向和反向Mamba共享占参数主体的输入、输出投影，但保留独立的depthwise convolution、SSM状态和时间离散化参数。这与公开Caduceus tied-projection实现一致：既降低参数量，又允许两个方向学习不同动力学。

### 2.3 为什么不用全注意力

128K全注意力的注意力矩阵随长度平方增长，在3×40GB A100上不适合作为3.3亿参数主体。Mamba selective scan对序列长度线性扩展；投影计算仍然较大，但不存在 `L×L` 注意力矩阵。

任何正式实现都不得在128K路径中偷偷加入全局quadratic attention。若需要局部融合，只能使用固定宽度卷积或有严格上界的局部操作。

## 3. 参数量精确合同

对一个方向的Mamba，设 `d=d_model`、`r=dt_rank`、`n=d_state`、`k=d_conv`、expansion=2。前后方向共享 `in_proj/out_proj`，其余参数独立。含每层RMSNorm后，单层独立参数为：

`P_layer = 6d² + 8dr + 12dn + 4dk + 13d`

代入 `d=1024,r=64,n=16,k=4`：

- 每层：7,042,048；
- 47层：330,976,256；
- 8-token embedding：8,192；
- final RMSNorm：1,024；
- 骨干合计：**330,985,472**。

该公式已用公开的 Caduceus `d_model=256,n_layer=16` 配置做交叉检查，得到7,725,312参数，与公开checkpoint元数据一致。

预训练临时head：

| head | 参数量 |
|---|---:|
| tied MLM bias | 8 |
| 9通道region head | 9,225 |
| 4类frame head | 4,100 |
| 6类boundary head | 6,150 |
| `1024→512→256` contrastive head | 656,128 |
| head合计 | 675,611 |

完整预训练计算图参数量为 **331,661,083**。论文和模型名使用“330M级”指骨干规模；不得把临时head删掉后声称训练图精确为330M。

## 4. 反向互补策略

### 4.1 采用PH式而非RCPS双通道

公开Caduceus的RCPS实现会把激活通道加倍，在128K和40GB显存条件下显著增加激活压力。本模型采用：

- 双向Mamba骨干；
- 每个训练anchor以0.5概率采用正向或reverse-complement方向；
- 5%的anchor同时计算两种方向并施加RC一致性损失；
- 下游正式预测对 `x` 与 `RC(x)` 的坐标对齐输出取平均，称为post-hoc conjoining。

因此，本模型可称“RC-consistent”或“RC-conjoined”，但**不能声称结构上严格RC等变**。论文必须把这一边界写清楚，并用RC一致性误差实测支持。

RC第二视图是额外forward compute：计入`processed_forward_tokens`、显存/吞吐和ETA，但不计为第二个unique corpus sample。实现不能为了保持日志里的名义tokens/s而漏报这部分计算。

### 4.2 对齐规则

- sequence-level输出：正向与RC的logit直接平均；
- base-level输出：先沿长度维反转RC输出，再按A↔T、C↔G和donor↔acceptor等标签映射后平均；
- frame输出：RC后必须按strand和codon相位重映射，不能只反转数组；
- 不对PAD、N和ignore位置计算RC一致性。

## 5. 预训练输出head

### 5.1 MLM head

- 输入：每个碱基位置的1,024维隐状态；
- 输出：8-token logits；
- 权重：与embedding共享；
- 有效target：A/C/G/T；N、PAD和ignore不计损失；
- 作用：学习十字花科序列分布、保守motif、局部和长程依赖。

### 5.2 Region head

9个可同时为真的通道：gene、exon、intron、CDS、5'UTR、3'UTR、ncRNA、TE、实验支持promoter。

使用多标签而不是互斥softmax，因为植物基因组存在重叠转录本、UTR/CDS层级、嵌套基因和TE插入。低可信或冲突位置用validity mask排除。

### 5.3 Frame head

输出 `frame0/frame1/frame2/non-CDS` 四类。只对高可信、strand已知的CDS和明确callable背景计算损失。RC后进行strand-aware相位映射。

### 5.4 Boundary head

6个独立通道：splice donor、splice acceptor、start codon、stop codon、TSS、TTS。采用稀疏二元head并配合匹配负例；缺少TSS/TTS实验证据的注释不能作为直接阳性。

### 5.5 Homeolog/ortholog head

- 先在有效基因体及两侧上下文上做mask-aware pooling；
- 两层投影 `1024→512→256`，中间SiLU，输出L2归一化；
- 共线ortholog/homeolog为positive；同家族非共线拷贝、相同GC/长度的邻近基因为hard negative；
- 仅用train内配对，不能连接到development或sealed test。

这个head是十字花科专属表示学习的重要组成，但最终是否改善下游必须由消融证明。

## 6. 表征读取接口

模型对下游提供四种冻结接口：

1. `per_base_hidden`：`B×L×1024`，用于分割、边界和profile；
2. `masked_mean_pool`：全窗口mask-aware均值，用于通用分类；
3. `multi_scale_pool`：1/4、1/16、1/64分辨率的分块均值，用于长程回归和3D结构；
4. `gene_anchor_pool`：基因体、上游、下游分别pool后拼接，用于表达、homeolog和功能任务。

不使用单侧CLS token，因为它会制造方向不对称。所有公共基线都要比较其官方pooling和统一mean pooling，不能只给本模型选择最有利读取方式。

## 7. 下游适配方式

同一任务按三个协议报告：

- **Linear probe**：骨干冻结，只训练线性或规定的小head；
- **Parameter-efficient tuning**：在输入/输出投影和norm上使用相同预算的adapter/LoRA；
- **Full fine-tuning**：仅在数据量足够且所有基线都可执行时报告。

禁止给本模型使用大head、给公共模型使用线性head。若某公共模型只提供API或不支持目标长度，则在“可比性/可执行性”列如实标记，不把缺失结果算作本模型获胜。

## 8. 128K显存与执行设计

### 8.1 核心原则

3.31亿参数的模型状态小于128K激活压力，但不能写成“天然能放下”。按训练图331,661,083参数和约16 bytes/parameter的保守状态预算，权重、梯度、FP32 master与Adam状态约4.94 GiB，尚未包括CUDA context、allocator碎片、kernel workspace和激活。

单条128K的`B×L×1024` bf16 hidden约0.25 GiB，FP32 residual约0.50 GiB。若朴素地为47个block都保存hidden+residual边界，理论边界量约35.25 GiB；因此逐block checkpoint不是正式方案。正式候选是按4–6层分组的hierarchical/selective checkpoint，并由真实100-step门禁在显存和重算成本之间冻结唯一配置。

正式实现必须包含：

- bf16参数和激活；
- FP32 residual；
- hierarchical/selective activation checkpoint，不保留47个逐层大边界；
- fused selective scan和RMSNorm；
- 前向、反向分支按可回收中间量的顺序执行；
- 按长度bucket，避免batch内padding；
- loss按位置分块计算，不能长期保留所有head的全精度logits；
- DDP三卡各持有完整模型，三个rank处理互不重复窗口。

### 8.2 不允许的“省显存”方式

- 不允许缩小层数或隐藏维后仍使用330M名称；
- 不允许把128K截成互不通信的短块却声称具有128K感受野；
- 不允许只做forward后声称可训练；
- 不允许用no-grad结构head冒充多任务反向；
- 不允许出现silent OOM retry后跳过长窗口；
- 不允许在不同rank上使用不同长度造成隐蔽的同步等待和样本丢弃。

若首选配置仍无法训练128K，修复顺序固定为：优化checkpoint分组/fused kernel、chunked head/scan、optimizer-state sharding、保持全局状态连续的sequence parallel。任何方案都必须通过远程依赖测试；若仍失败，正式状态为BLOCKED。

## 9. 初始化和数值稳定性

- embedding正态初始化，标准差0.02；
- 输入/输出投影按Mamba实现初始化；
- 残差输出投影按层数做 `1/sqrt(n_layer)` 缩放；
- RMSNorm epsilon固定 `1e-5`；
- residual保持FP32；
- 梯度norm在clip前记录，clip阈值1.0；
- 每个loss分别检查NaN/Inf，不能只检查总loss；
- 结构head类别权重只从train统计，且设置上限，防止极稀有边界产生爆炸梯度。

## 10. 架构级验收测试

这些测试使用完整331M训练图，不构成另一个模型版本：

1. **参数合同**：可训练参数必须等于331,661,083；若实现依赖造成偏差，必须逐张量解释并更新文档后才能训练。
2. **词表remap**：已知 `ACGTN` raw编码必须映射到 `1,2,3,4,5`，PAD计数为0。
3. **双向性**：改变窗口左端和右端都应影响中心表示；禁用反向分支应被测试捕获。
4. **RC坐标**：正向和RC的base-level标签、frame和boundary映射逐位可逆。
5. **长度**：六种正式长度各至少10个optimizer steps；128K连续100步，在第50步保存、从新进程exact resume后完成余下50步。
6. **远程依赖**：central output对距离超过32K的位置具有非零梯度/干预响应；nested-window、remote-flank mask/shuffle和counterfactual replacement共同排除“只接受长tensor但只用局部序列”。
7. **线性复杂度**：显存与时间随长度的实测趋势不能出现quadratic attention特征。
8. **checkpoint重现**：同一batch在保存/恢复后的loss、梯度和sampler cursor在规定容差内一致。
9. **DDP无重复与归一化**：三个rank的anchor集合交集为空；按全局有效目标数归一化后的梯度与单进程参考在容差内一致。
10. **ignore语义**：N、PAD、未知注释和冲突注释不会进入任何错误分母。
11. **全头反向**：MLM、region、frame、boundary、RC和homeolog head均有真实梯度；没有标签的head梯度为无贡献而不是伪0标签。

## 11. 必须保留的消融

只在冻结development上做模型机制分析，sealed test不用于选消融：

- 同架构随机初始化；
- 去掉结构监督；
- 去掉homeolog对比目标；
- 去掉RC一致性但保留随机RC；
- 单向Mamba；
- 最大32K与完整128K；
- 不做属/assembly平衡；
- 有近重复聚类与不做近重复聚类的泄漏敏感性分析只能用于展示风险，后者不能成为主结果。

主文公共模型比较与内部消融分表报告，不能用多个内部变体挤掉强公共基线。

## 12. 预期优势与明确边界

### 12.1 预期但尚未证实的优势

- 对十字花科基因结构、剪接和启止边界的跨物种迁移；
- 对U三角多倍体homeolog、亚基因组来源和共线保留的表征；
- 对NLR/抗病基因簇、S-locus、硫代葡萄糖苷和开花调控长区域的建模；
- 对PAV/SV/TE邻域及远端调控的128K上下文利用；
- 在较少标注数据下优于通用人类或全植物模型。

### 12.2 不能提前声称

- 不能称严格RC等变；
- 不能称拥有AlphaGenome式数千功能track输出；
- 不能称拥有Evo 2式1M上下文或生成能力；
- 不能因模型来自十字花科语料就自动声称“十字花科基础模型有效”；
- 不能把结构监督head的存在写成结构任务已经完成；
- 不能把3张A100的计划写成已验证吞吐或已完成训练。
- 不能把同一预训练backbone上的五个下游seed写成五个独立基础模型seed。

### 12.3 架构创新边界

双向tied-projection Mamba本身来自Caduceus路线，本项目不把已有SSM方程重新命名为全新架构。首篇论文的主要方法创新应定位为：十字花科专属、去重和暴露审计后的统一超长语料；结构与homeolog联合目标；防泄漏的U三角/多倍体/专属性状任务；以及在3×40GB条件下可复现的128K训练系统。只有新增模块经过同数据、等token消融证明后，才可单独提出“新神经网络模块”主张。

同理，公共植物模型与本模型同时改变了架构、语料和token预算，不能单独识别“十字花科语料”的因果贡献。若不增加一个同架构、同QC、同token的广义植物语料控制预训练，论文应把创新表述为专属系统与专属证据体系，而不是语料单因素因果结论。

只有完整训练、同数据公平重跑、五个下游训练seed和严格生物split结果共同支持后，才可形成正式模型主张；这不替代前述单一预训练lineage局限。
