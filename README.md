# BrassicaceaeGenomeFM — 十字花科基因组基础模型

## 当前状态

| 项目 | 状态 |
|------|------|
| 模型 | BrassiCaduceus ~330M（Bi-Mamba2 + tied embedding） |
| 训练 | **已直接切换为恒定2e-5** — 从step 56,500建立第三条lineage |
| 上下文 | 4K / 8K / 16K / 32K / 64K（128K 因40GB显存上限未纳入v1） |
| 新学习率 | 每一步恒定2e-5；无warmup、无衰减、无自动重启、无开发集变差回退 |
| 开发集 MLM | 最新1.22863（step 59,000）；恒定2e-5分支5点轻微下降，全程最佳1.22078（step 11,000） |
| 活跃语料覆盖 | 464.5亿 / 1142亿唯一tokens（40.7%）；cycle 0、无受控复用 |
| Checkpoint | 恒定2e-5新lineage已保存5个永久checkpoint，最新step 59,000；父checkpoint step 56,500保留 |
| GPU | gpu10的GPU 0/1/2，均为A100 40GB，当前100%利用率 |
| CPU Gate | 328/328 tests PASSED；恒定2e-5新lineage专属Gate已通过 |
| 下游任务 | 32 项任务体系，12 个数据 release 已冻结（521,204 样本） |
| 公共基线 | 14 个公共 DNA-FM 权重就位于 `~/myhermes/down_model` |

## 关键参数

- 架构：21层 Bi-Mamba2, d_model=768, d_state=128, group_size=6
- 并行：FSDP (FULL_SHARD), 3 GPU, world_size=3
- 精度：bfloat16 参数+激活, float32 残差累积
- 优化器：AdamW, peak lr=3e-4, warmup=1000 steps, WSD schedule
- 每 step token 数：786,432
- gradient_accumulation=4, per_rank microbatch: 16/8/4/2/1 (4K→64K)
- RC 仅在 4K–64K 启用, fraction=0.05

## 损失函数

| 损失 | 权重 | 说明 |
|------|------|------|
| MLM | 1.0 | 15% 掩码, span+singleton |
| Region | 0.25 | 9类基因组区域分类 |
| Frame | 0.1 | 6-frame ORF 检测 |
| Boundary | 0.1 | 区域边界 token 检测 |
| RC | 0.05 | 反向互补一致性 |
| Homeolog | 0.05 | 同源基因对 InfoNCE |

## 产物路径

- 活跃训练日志：`workspace/formal_runs/brassicaceae_330m_constant2e5_from_step56500_v1/training.jsonl`
- 活跃checkpoint：`workspace/formal_runs/brassicaceae_330m_constant2e5_from_step56500_v1/checkpoints/step_NNN/`
- 父checkpoint：`workspace/formal_runs/brassicaceae_330m_low_lr_from_step41500_v1/checkpoints/step_000000056500/`
- 上一分支checkpoint：`workspace/formal_runs/brassicaceae_330m_formal_v1/checkpoints/step_000000041500/`
- 训练曲线：`docs/brassicaceae_genomefm_v1_training_curves_step*.png/pdf`（最新随提交更新）

## 训练进度（恒定2e-5分支快照至step 59,078）

![训练曲线 step 59078](docs/brassicaceae_genomefm_v1_training_curves_step59078.png)

### 白话解读

**A. 全部上下文的训练 MLM（左上）**
恒定2e-5分支已从step 56,500连续运行2,578步，最近50步训练MLM均值1.095，较切换前约1.104下降约0.8%。训练曲线保持平滑，没有出现把学习率翻倍后的震荡或发散。

**B. 五档上下文（右上）**
恒定2e-5分支最近50个各自上下文点约为4K 1.099、8K 1.103、16K 1.105、32K 1.101、64K 1.099，五档差距约0.006；长上下文依然稳定，没有长度选择性退化。

**C. 多轮 WSD 学习率（左下）**
绿色线是step 41,500的单向低学习率分支；紫色线是step 56,500的新恒定2e-5分支。新lineage从父checkpoint的1e-5直接切到2e-5，从step 56,501开始每一步都严格保持2e-5；没有warmup、衰减、自动重启或开发集触发回退。

**D. 开发集（右下）**
恒定2e-5分支已有5个固定开发集点：1.22907、1.22901、1.22886、1.22882、1.22863，呈轻微下降。首末下降0.00043，最新点比父checkpoint的1.22875低0.00012，但仍高于低学习率分支step 56,000的1.22856，也远未超过全程最佳1.22078；目前只能称为微弱正向趋势。

### 当前判断

- **运行层面健康**：恒定2e-5已连续运行2,578步，3个FSDP rank和三张A100保持满载，无失败、无复用。
- **优化层面有提升**：训练MLM较切换前下降约0.8%，五档上下文同步稳定。
- **泛化提升仍很小**：开发集仅出现0.00043的缓慢下降，尚未形成新的开发集最佳；按用户要求继续恒定2e-5，不设置自动降回1e-5。

- CPU Gate：`workspace/release/formal_cpu_gate_constant2e5_from_step56500_v1/`

## 启动命令

```bash
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel
CUDA_VISIBLE_DEVICES=0,1,2 PYTHONPATH=workspace/code \
python workspace/code/formal_launcher.py \
  --run-contract workspace/config/formal_run_constant2e5_from_step56500_v1.json \
  --checkpoint-group-size 6 \
  --distributed-mode fsdp \
  --resume workspace/formal_runs/brassicaceae_330m_low_lr_from_step41500_v1/checkpoints/step_000000056500 \
  --authorize-gpu-launch I_AUTHORIZE_3XA100_FORMAL_TRAINING
```

## 训练集

- 66个十字花科 genome assembly
- 不含放回抽样, cycle 0
- cluster-aware split (train/development)
- 5个上下文长度的 token 比例: 4K=10%, 8K=20%, 16K=21%, 32K=27%, 64K=22%
