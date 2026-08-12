# BrassicaceaeGenomeFM v1 训练进度

## 当前状态 (2026-08-11 19:20)

- **Step**: 1,821
- **运行时长**: ~50分钟（当前会话）
- **GPU**: ibgpu10, 3×A100 40GB (GPU 0/1/2)
- **模式**: FSDP FULL_SHARD
- **32K/64K context**: 仅 MLM loss（位置辅助损失需修复 collator）
- **Homeolog**: 部分 pair 端点 OOB 已修复，OOB pair 被安全跳过

## 门禁链

| 门禁 | 状态 | 产物 |
|------|------|------|
| Development 索引 | ✅ | catalog_index_development_v1 |
| CPU Gate | ✅ 302/302 | formal_cpu_gate_v1 |
| Training Readiness | ✅ | formal_training_readiness_v1 |
| GPU Preflight | ✅ | preflight receipt |
| GPU Acceptance (64K) | ✅ | acceptance receipt |
| 正式训练 | ▶️ 进行中 | step 1821+ |

## 迭代历史

### v1.0 — 正式 v1 启动

**关键修复**:
1. 128K→64K: 40GB A100 不支持 128K Mamba backward（~512 MiB OOM）
2. gradient_accumulation 2→4: 64K microbatch 1→1 不变，其余减半以保持 token/step=786,432
3. DDP→FSDP: tied embedding 在 DDP 下导致 mlm_bias 重复梯度标记，切 FSDP 解决
4. checkpoint_group_size 5→6: RC + 共享投影省 ~512 MiB
5. Pair OOB: 正边端点超界时返回全零有效性掩码（被 homeolog loss 自动跳过）

**启动参数**:
```
checkpoint_group_size=6
distributed_mode=fsdp
gradient_accumulation=4
per_rank_microbatch: 16/8/4/2/1 (4K→64K)
RC fraction=0.05 (仅 ≤64K)
```

## Checkpoint

| Step | 路径 | 状态 |
|------|------|------|
| 500 | checkpoints/step_000000000500 | ✅ 永久保存 |
| 1000 | checkpoints/step_000000001000 | ✅ 永久保存 |
| 1500 | checkpoints/step_000000001500 | ✅ 永久保存 |
| 2000 | 进行中 | ~step 2000 |

## 已知问题

1. **32K/64K 缺少位置损失**: collator 对超过 8192 的 context 未产出 region/frame/boundary 标签
2. **Homeolog loss 平坦**: mean ~0.693 (= -ln(1/N) with N=1, 退化为均匀分布)，模型尚未学会区分同源对
3. **MLM loss 震荡**: 32K/64K 的 loss 波动较大 (1.3–1.8)，与梯度噪声有关
4. **128K 缺失**: 需 80GB GPU 或更激进的 activation checkpointing
