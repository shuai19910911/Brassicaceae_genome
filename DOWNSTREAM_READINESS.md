# 下游数据 release 状态（2026-08-14）

全部 release 已冻结：固定 train/validation/test split，经泄漏审计（样本ID唯一、RC序列不跨split、生物组不跨split、坐标不重叠），目录只读，含 manifest.json / receipt.json / samples.jsonl。

| release | 任务 | 样本数 | dataset_root_hash |
|---|---|---|---|
| p10a_species_v1 | P10 | 24,000 | `fc4d753cae07189a…` |
| p10b_species_v1 | P10 | 18,000 | `c2b56dc202cde80b…` |
| p13_core_promoter_v1 | P13 | 12,000 | `dd669964b90f3965…` |
| p13_promoter300_v1 | P13 | 18,000 | `f36a99147a906bc1…` |
| p13a_iprowael_tata_nontata_v1 | P13 | 16,182 | `9ab88b40f200fa4d…` |
| p1_coding_intergenic_v1 | P1 | 24,000 | `bfb48cff590a66a7…` |
| p3_splice_acceptor_v1 | P3 | 18,000 | `af42ee455defa716…` |
| p3_splice_donor_v1 | P3 | 18,000 | `d956271d356edad9…` |
| p4_region_type_v1 | P4 | 24,000 | `9ddf1cb2f65397a0…` |
| p8_4mc_athaliana_v1 | P8 | 223,850 | `90ceb5147aa9c1d1…` |
| p8_4mc_geum_pickeringii_v1 | P8 | 34,362 | `c51b16b1b3db070e…` |
| p8_4mc_geum_subterraneus_v1 | P8 | 90,810 | `6aaf3c842135ade6…` |

合计 **12** 个 release，**521,204** 个样本。

**身份链验证**（2026-08-14）：全部 12 个 release 已通过 `load_downstream_dataset_release` 完整身份校验（registry 定义哈希、release id、root hash、只读位、文件闭包、逐文件 sha256），且 registry 身份哈希已修复为不随 release 索引增长而漂移（回归测试 test_registry_sha256_is_stable_when_release_index_grows）。

## 启动方式（等用户指定执行卡）

1. 指定 GPU 卡后，在对应卡上运行下游评测（本模型 frozen encoder + 公共模型编码）；
2. 剩余 CPU 步骤提交 q03；
3. 正式训练 checkpoint（每500步永久保存）与评测并行。

## 公共基线模型（统一从 down_model 调用）

全部 14 个公共 DNA 基础模型权重已就位于 **~/myhermes/down_model/**（该目录是模型唯一存放处，各模型带 download_receipt.json，整体 COPY_RECEIPT.json=verified）：

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

下游评测时直接从此目录加载，不复制、不重复下载。

