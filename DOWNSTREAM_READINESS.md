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

## 启动方式（等用户指定执行卡）

1. 指定 GPU 卡后，在对应卡上运行下游评测（本模型 frozen encoder + 公共模型编码）；
2. 剩余 CPU 步骤提交 q03；
3. 正式训练 checkpoint（每500步永久保存）与评测并行。

