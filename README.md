# BrassicaceaeGenomeFM — 十字花科基因组基础模型

## 当前状态

| 项目 | 状态 |
|------|------|
| 模型 | BrassiCaduceus ~330M (Bi-Mamba2 + tied embedding) |
| 训练 | **进行中** — step 1820+, FSDP 3×A100 40GB |
| 上下文 | 4K / 8K / 16K / 32K / 64K (128K 待更多显存) |
| MLM loss | 最新 ~1.3–1.6（稳定下降中） |
| Checkpoint | 每 500 step 永久保存 (step 500/1000/1500 已存) |
| GPU 节点 | ibgpu10 (12.12.12.210), GPU 0/1/2 |
| CPU Gate | 302/302 tests PASSED |

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

- 训练日志：`workspace/formal_runs/brassicaceae_330m_formal_v1/training.jsonl`
- Checkpoint：`workspace/formal_runs/brassicaceae_330m_formal_v1/checkpoints/step_NNN/`
- 训练曲线：`workspace/figures/brassicaceae_genomefm_v1_training_curves_step*.png`
- CPU Gate：`workspace/release/formal_cpu_gate_v1/`

## 启动命令

```bash
cd /home/user/zhangzhishuai/myhermes/Brassicaceae_genomemodel
CUDA_VISIBLE_DEVICES=0,1,2 PYTHONPATH=workspace/code \
python workspace/code/formal_launcher.py \
  --run-contract workspace/config/formal_run_v1.json \
  --checkpoint-group-size 6 \
  --distributed-mode fsdp \
  --authorize-gpu-launch I_AUTHORIZE_3XA100_FORMAL_TRAINING
```

## 训练集

- 66个十字花科 genome assembly
- 不含放回抽样, cycle 0
- cluster-aware split (train/development)
- 5个上下文长度的 token 比例: 4K=10%, 8K=20%, 16K=21%, 32K=27%, 64K=22%
