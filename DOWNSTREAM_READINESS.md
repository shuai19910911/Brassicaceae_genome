# 下游数据 release 状态（更新至2026-09-02）

下表列出的12个release已全部冻结：固定train/validation/test split，经泄漏审计（样本ID唯一、RC序列不跨split、生物组不跨split、坐标不重叠），目录只读，含manifest.json / receipt.json / samples.jsonl。这里的“全部”仅指这12个已构建release，不代表32项任务都已有数据。

| release | 任务 | 样本数 | dataset_root_hash |
|---|---|---|---|
| p10a_species_v1 | P10 | 24,000 | `33a4869eebb6e774…` |
| p10b_species_v1 | P10 | 18,000 | `2e838786bb67efcf…` |
| p13_core_promoter_v1 | P13 | 12,000 | `7b95dc1855f361bf…` |
| p13_promoter300_v1 | P13 | 18,000 | `9c3ad0c66b15c0fa…` |
| p13a_iprowael_tata_nontata_v1 | P13 | 16,182 | `9ab88b40f200fa4d…` |
| p1_coding_intergenic_v1 | P1 | 24,000 | `f89151590c93d82b…` |
| p3_splice_acceptor_v1 | P3 | 18,000 | `e5307830de8a6fb3…` |
| p3_splice_donor_v1 | P3 | 18,000 | `3c878fe3a27ce874…` |
| p4_region_type_v1 | P4 | 24,000 | `9133046c93118ffc…` |
| p8_4mc_athaliana_v1 | P8 | 223,850 | `90ceb5147aa9c1d1…` |
| p8_4mc_geum_pickeringii_v1 | P8 | 34,362 | `c51b16b1b3db070e…` |
| p8_4mc_geum_subterraneus_v1 | P8 | 90,810 | `6aaf3c842135ade6…` |

合计 **12** 个release、**521,204**个样本，覆盖P1/P3/P4/P8/P10/P13六项任务；其余26项任务的数据仍为`NOT_FROZEN`。

**身份链验证**（2026-08-14）：全部 12 个 release 已通过 `load_downstream_dataset_release` 完整身份校验（registry 定义哈希、release id、root hash、只读位、文件闭包、逐文件 sha256），且 registry 身份哈希已修复为不随 release 索引增长而漂移（回归测试 test_registry_sha256_is_stable_when_release_index_grows）。

## 当前执行闭包

- Registry：32项任务×27种方法，共864个单元。
- 实现状态：154 ready、536 blocked、174 not applicable。
- 现有12个release按当前ready方法可展开57次真实运行。
- 正式下游结果仍为0：当前没有已完成的模型分数或排行榜。

## 启动方式（等用户指定执行卡）

1. 指定 GPU 卡后，在对应卡上运行下游评测（本模型 frozen encoder + 公共模型编码）；
2. 剩余 CPU 步骤提交 q03；
3. 正式训练 checkpoint（每500步永久保存）与评测并行。

## 公共基线模型（统一从 down_model 调用）

全部14个公共DNA基础模型权重已就位于 **~/myhermes/down_model/**（该目录是模型唯一存放处，各模型带download_receipt.json，整体COPY_RECEIPT.json=verified）。这证明权重资产完整，不等于所有适配器、真实GPU forward或正式评测已经闭环：

| 模型 | down_model 目录 | 说明 |
|---|---|---|
| AgroNT 1B | AgroNT_1B | 农业基因组模型 |
| DNABERT-2 117M | DNABERT2 | BPE 基因组 LM |
| NT v2 500M multi-species | NTv2_500M_multi_species | 多物种核甘酸转换器 |
| HyenaDNA medium 160K | HyenaDNA_medium_160k | 长上下文卷积 LM |
| GPN-Brassicales | GPN_Brassicales | 十字花科专属 GPN |
| PlantCAD2-M/L | PlantCAD2_Small、PlantCAD2_Large | 植物长程模型双规格 |
| PlantCaduceus | PlantCaduceus_l32 | 植物双向 Mamba |
| Caduceus-PS | Caduceus_Ph_131k_d_model256 | 植物噬菌体基准 |
| Evo 2 1B | Evo2_1B_base | 基因组序列模型 |
| GENA-LM / PlantBiMoE / PlantDNAMamba_BPE / PlantNT_singlebase | 同名目录 | 备用基线 |

下游评测时直接从此目录加载，不复制、不重复下载。只有完成模型适配、真实forward、相同split/head预算和正式receipt后，才能计入公共基线结果。

