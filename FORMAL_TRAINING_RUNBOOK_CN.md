# BrassicaceaeGenomeFM 正式训练一键启动手册

本手册只用于当前唯一正式lineage：`brassicaceae_330m_formal_v1`。

## 现在不要启动

在用户明确说GPU 0、1、2已经空出并授权正式训练之前，只能运行dry-run。dry-run不会创建CUDA context，不会占显存，也不会启动torchrun。

```bash
PYTHONPATH=workspace/code /home/user/zhangzhishuai/.local/share/mamba/envs/zuowu_genomemodel/bin/python3.10 \
  workspace/code/formal_launcher.py \
  --run-contract workspace/config/formal_run_v1.json \
  --checkpoint-group-size 5 \
  --dry-run
```

## GPU空出后的一条启动命令

收到用户明确启动指令后执行：

```bash
PYTHONPATH=workspace/code /home/user/zhangzhishuai/.local/share/mamba/envs/zuowu_genomemodel/bin/python3.10 \
  workspace/code/formal_launcher.py \
  --run-contract workspace/config/formal_run_v1.json \
  --checkpoint-group-size 5 \
  --authorize-gpu-launch I_AUTHORIZE_3XA100_FORMAL_TRAINING
```

启动器自动完成：

1. 验证正式bundle及独立PASS回执；
2. 验证train/development mmap索引和bundle根身份；
3. 验证模型、训练、pair和代码hash；
4. 用`nvidia-smi`确认物理GPU 0、1、2均为A100 40GB；
5. 确认三卡无compute PID且每卡已用显存低于1,024 MiB；
6. 写入绑定代码、配置、GPU身份和`checkpoint_group_size`的一次性`PASS_GPU_PREFLIGHT`回执；旧回执内容寻址归档，不覆盖历史；
7. 设置`CUDA_VISIBLE_DEVICES=0,1,2`，三个rank在创建CUDA context前再次并行探测空闲状态，并用CPU-only FileStore汇合；
8. 直接`torchrun --nproc-per-node=3`启动；先以真实128K窗口、强制RC视图、homeolog pair和零学习率临时AdamW完成前向、反向、梯度裁剪与优化器显存验收；
9. 验收PASS后发布只读GPU acceptance回执，销毁临时optimizer，再创建全新的正式optimizer，从step 1连续训练，不再开发代码。

默认`--checkpoint-group-size 5`。4、5、6都已作为同一冻结代码身份下的允许候选；如果真实GPU acceptance显示默认值显存不足，可直接用同一命令改为4或6重新启动，无需修改代码、配置或重新排q05 Gate。正式checkpoint会记录实际选择，恢复时必须传入同一数值。

CPU Gate、lineage、代码身份或GPU空闲检查失败时，会在创建训练进程前停止，不抢卡、不杀进程。真实128K acceptance若失败，torchrun会在正式optimizer和step 1之前退出；此时已短暂创建CUDA context，但不会留下正式训练状态或伪checkpoint。

## 精确恢复

只能从同一formal run、同一bundle根身份的完整checkpoint恢复：

```bash
PYTHONPATH=workspace/code /home/user/zhangzhishuai/.local/share/mamba/envs/zuowu_genomemodel/bin/python3.10 \
  workspace/code/formal_launcher.py \
  --run-contract workspace/config/formal_run_v1.json \
  --resume workspace/formal_runs/brassicaceae_330m_formal_v1/checkpoints/step_000000000500 \
  --checkpoint-group-size 5 \
  --authorize-gpu-launch I_AUTHORIZE_3XA100_FORMAL_TRAINING
```

恢复会先在CPU侧验证不可变checkpoint envelope、run/release、500-step边界、DDP/FSDP模式和`checkpoint_group_size`，再校验并恢复模型、optimizer、context scheduler、各context cycle/cursor、pair cycle、WSD、development monitor、每个rank自己的CPU/当前CUDA RNG和三token账本。release、lineage或执行几何不一致会直接拒绝。

## 运行中产物

- 训练日志：`workspace/formal_runs/brassicaceae_330m_formal_v1/training.jsonl`
- 永久checkpoint：`workspace/formal_runs/brassicaceae_330m_formal_v1/checkpoints/step_<12位step>/`
- GPU预检回执：`workspace/formal_runs/brassicaceae_330m_formal_v1/preflight/receipt.json`

日志逐step记录context、coverage cycle、学习率、loss、有效目标数、梯度范数和三套token账。

## 中断语义

第一次SIGTERM/SIGINT不会在半个optimizer step写伪checkpoint。程序会完成当前step，并运行到下一个500步永久边界后退出。checkpoint永不覆盖。

如节点有硬时限，应在剩余时间足够到达下一个500步边界时提前发送SIGTERM。

## 训练何时停止

没有预定总step/token上限。训练只使用development证据触发WSD：

- 500步评估一次；
- 1,000步warmup后才允许触发；
- 连续10次未达到0.2%相对改善，或5个评估点内train改善而development恶化达到1%，触发decay；
- 触发后运行10,000步cosine decay至3e-5并停止。

训练期间不读取sealed test或acceptance。
