---
id: arch-fermi
name: Fermi
year: 2010
tags: 首个完整 GPU 计算架构
image: fermi_sm.png
---

### SM 配置
- Warp Scheduler: 2
- CUDA Core: 32
- LD/ST Unit: 16
- SFU: 4

### 说明
- Fermi 是 NVIDIA 第一个面向通用计算设计的完整架构。每个 SM 包含 32 个 CUDA Core，分布在 2 条 lane 上（每条 16 个）。

- 每个 CUDA Core 内部是 **1 个单精度浮点单元 (FPU) + 1 个整数单元 (ALU)**，可以直接执行 FMA（乘累加）操作。每个 cycle 可跑 16 个双精度 FMA。

- 寄存器文件 32768 × 32-bit，底部是 64KB Shared Memory / L1 Cache。

---

---
id: arch-kepler
name: Kepler
year: 2012
tags: SMX, 双精度黄金时代
image: kepler_sm.png
---

### SM 配置
- Warp Scheduler: 4
- CUDA Core: 192
- FP64 Unit: 64
- Dispatch Unit: 8
- LD/ST Unit: 32
- SFU: 32

### 说明
- SM 更名为 **SMX**。相比 Fermi 大幅堆料：CUDA Core 从 32 暴增到 192（4 × 3 × 16，每条 lane 仍是 16 个）。

- 最关键的变化：**独立的 64 个双精度运算单元**，不需要通过单精度单元去做双精度运算。这使得 Kepler 的双精度性能远超前后几代。4 个 Warp Scheduler 搭配 8 个 Dispatch Unit（1:2 比例）。

---

---
id: arch-maxwell
name: Maxwell
year: 2014
tags: SMM, 能效比优先
image: maxwell_sm.png
---

### SM 配置
- Warp Scheduler: 4
- CUDA Core: 128
- FP64 Unit: 0
- Dispatch Unit: 8
- LD/ST Unit: 32
- SFU: 32

### 说明
- SM 更名为 **SMM**。开始做减法：**移除独立双精度计算单元**，CUDA Core 从 192 精简到 128（4 × 32）。

- 工艺提升带来的收益：每个 CUDA Core 性能比 Kepler 提升 **1.4x**，整体能效比提升 **2x**。SMM 采用 4 个 Processing Block，每个 Block 有独立的 Warp Scheduler、Instruction Buffer 和 Register File。

---

---
id: arch-pascal
name: Pascal
year: 2016
tags: FP16, NVLink
image: pascal_sm.png
---

### SM 配置
- Warp Scheduler: 2
- CUDA Core: 64
- FP64 Unit: 32
- Dispatch Unit: 4
- LD/ST Unit: 16
- SFU: 16

### 说明
SM 内部进一步精简：2 × 32 = 64 CUDA Core，Warp Scheduler 也缩减为 2 个。但有两个重要变化：

- **双精度回归**：32 个独立 FP64 单元（2 × 16）
- **FP16 支持**：CUDA Core 首次支持半精度计算，为后续 AI 加速铺路
- **NVLink**：首次引入 GPU 间高速互联

### SM 微架构图
[image: pascal_sm_arch.png]

---

---
id: arch-volta
name: Volta
year: 2017
tags: V100, Tensor Core 诞生
image: volta_sm.png
---

### SM 配置
- Warp Scheduler: 4
- FP32 Core: 64
- INT32 Core: 64
- FP64 Core: 32
- Tensor Core: 8 [highlight]
- LD/ST / SFU: 32 / 16

### 说明
**里程碑架构。**三大关键变化：

- **CUDA Core 拆分**：不再是统一的 FPU+ALU，而是独立的 FP32 Core 和 INT32 Core。优势：**两者可以同时执行**，混合运算吞吐翻倍
- **Tensor Core 引入**：每个 SM 8 个（4 × 2），每个 TC 每周期执行 4×4×4 GEMM（FP16 输入，FP32 累加），等效 64 个 FP32 ALU
- **独立线程调度**：每个线程拥有独立 PC 和调用栈

Warp Scheduler 变为 1:1 对应 Dispatch Unit（之前是 1:2），并增加 L0 ICache。

### SIMT 改进：独立线程调度
[images: simt_old.png | simt_volta.png]
[captions: Pascal 及之前：分支两侧串行执行 | Volta：独立 PC + __syncwarp()，分支可交错调度]

Pascal 及之前，一个 Warp 遇到分支时两侧只能串行执行。Volta 将 PC 和调用栈设计为每个线程独立，分支内的指令可以在更细的粒度上混合调度，并支持 `__syncwarp()` 显式同步。

---

---
id: arch-turing
name: Turing
year: 2018
tags: RTX 20 系列, RT Core
image: turing_sm.png
---

### SM 配置
- Warp Scheduler: 4
- FP32 Core: 64
- INT32 Core: 64
- Tensor Core: 8 [highlight]
- LD/ST / SFU: 16 / 16

### 说明
- 最大改动是引入 **RT Core**（光线追踪加速单元）。SM 内计算单元与 Volta 类似，每个 SM 含 4 个 Processing Block：

- 每个 Processing Block：1 Warp Scheduler + 1 Dispatch Unit + 16 FP32 + 16 INT32 + **2 Tensor Core** + 4 LD/ST + 4 SFU

- Tensor Core 第二代：在 Volta 基础上**新增 INT8 和 INT4 支持**，开始覆盖推理量化场景。

### SM 微架构图
[image: turing_sm_arch.png]

---

---
id: arch-ampere
name: Ampere
year: 2020
tags: A100 / RTX 30, 稀疏 Tensor Core
image: ampere_sm.png
---

### SM 配置
- Warp Scheduler: 4
- FP32 Core: 64
- INT32 Core: 64
- FP64 Core: 32
- Tensor Core: 4 [highlight]
- LD/ST / SFU: 32 / 16

### 说明
- 每个 Processing Block：1 Warp Scheduler + 1 Dispatch Unit + 16 FP32 + 16 INT32 + 8 FP64 + **1 Tensor Core** + 8 LD/ST + 4 SFU

- Tensor Core 数量从 8 减半到 4，但**每个吞吐量翻 4 倍**，总吞吐翻倍。数据类型大幅扩展：FP16、BF16、TF32、FP64、INT8、INT4、Binary。

### GA 102 SM 微架构图
[image: GA102_sm.png]

### A100 vs V100 性能提升
[image: a100_vs_v100.png]


---

---
id: arch-ada
name: Ada Lovelace
year: 2022
tags: RTX 40 系列, FP8 / DLSS 3
image: ada_sm.png
---

### SM 配置
- Warp Scheduler: 4
- FP32 Core: 128
- INT32 Core: 64
- Tensor Core (4th): 4 [highlight]
- FP64 Core: 2
- LD/ST / SFU: 32 / 16

### 说明
**消费级旗舰。**延续 Ampere 的双数据通路（64 专用 FP32 + 64 Flex FP32/INT32），合计 128 FP32 Core。TSMC 4N 工艺。

- **第 4 代 Tensor Core：**新增 FP8（E4M3 / E5M2）支持，搭载 Hopper 的 Transformer Engine 技术。吞吐量相比 Ampere 再翻倍。

- **第 3 代 RT Core：**新增 Opacity Micro-Map（OMM）和 Displaced Micro-Mesh Engine，光追性能 2x。

- **L2 缓存大幅扩容：**AD102 达 96MB（Ampere GA102 仅 6MB，16x 增长），显著减少显存访问。

- 支持 DLSS 3（帧生成）、Shader Execution Reordering（SER，光追调度优化）。

- **AD102**：144 SM，18,432 FP32 Core，576 TC。
- **RTX 4090**：128 SM，16,384 FP32 Core。

---

---
id: arch-hopper
name: Hopper
year: 2022
tags: H100 / H200, Transformer Engine
image: hopper_sm.png
---

### SM 配置
- Warp Scheduler: 4
- FP32 Core: 128
- INT32 Core: 64
- FP64 Core: 64
- Tensor Core (4th): 4 [highlight]
- LD/ST / SFU: 32 / 16

### 说明
**大模型时代的数据中心旗舰。**FP64 Core 翻倍至 64（vs Ampere 32），Shared Memory + L1 扩大至 256KB。

- **第 4 代 Tensor Core：**原生 FP8 支持（E4M3 / E5M2），引入 `wgmma`（Warp Group MMA）指令，128 线程协作完成矩阵运算。FP16 吞吐 729 TFLOPS，FP8 达 1,448 TFLOPS（H800）。

- **Transformer Engine：**硬件动态精度选择，每层自动在 FP8 和 FP16 之间切换，训练精度不损失。

- **Thread Block Cluster：**跨 SM 的线程块协作原语。

- **Distributed Shared Memory (DSMEM)：**SM 间可直接访问彼此的 Shared Memory，延迟 180 cycles，带宽 3.27 TB/s。

- **Tensor Memory Accelerator (TMA)：**异步 1D-5D 张量搬运，解放计算线程。

- **DPX 指令集：**动态规划算法加速（Smith-Waterman 等），最高 13x 提速。

- **H100 SXM5**：132 SM，16,896 FP32 Core，528 TC，80GB HBM3（3 TB/s），50MB L2，800 亿晶体管，TSMC N4。


### CUDA Kernel
CUDA Kernel 之前是三个层次：Grid、Thread Block 和 Thread，分别对应整个 GPU、SM 和 CUDA Core，而这一代引入了 Thread Block Cluster 的层次，变成了四个层次：Grid、Thread Block Cluster、Thread Block 和 Thread。（H100 introduces a new Thread Block Cluster architecture that exposes control of locality at a granularity larger than a single Thread Block on a single SM.）其中 Thread Block 对应 GPC，每个 GPC 有多个 TPC，每个 TPC 有多个 SM。（The Clusters in H100 run concurrently across SMs within a GPC. A GPC is a group of SMs in the hardware hierarchy that are always physically close together.）


---

---
id: arch-blackwell
name: Blackwell
year: 2024
tags: B100 / B200, FP4 / TMEM
---

### SM 配置
- Warp Scheduler: 4
- FP32 Core: 128
- INT32 (统一): 128
- Tensor Core (5th): 4 [highlight]
- TMEM (新增): 256KB
- SMEM + L1: 228KB

### 说明
**双芯片封装，2080 亿晶体管。**INT32 和 FP32 执行路径统一，INT32 Core 数量与 FP32 持平。

- **第 5 代 Tensor Core：**全新 FP4（e2m1）和 FP6（e3m2 / e2m3）支持。FP4 吞吐 7,702 TFLOPS，FP8 吞吐 3,851 TFLOPS（B200）。引入 `tcgen05.mma` 单线程 tensor 指令，替代 warp 级 MMA，延迟从 32 cycles 降至 11 cycles。

- **Tensor Memory (TMEM)：**全新的 256KB 专用 Tensor Core 存储，512 列 × 128 lane 的 2D 阵列。读带宽 16 TB/s，写带宽 8 TB/s（每 SM）。缓存未命中延迟降低 58%。

- **硬件解压引擎：**原生支持 LZ4、Snappy、Zstd、GZIP 解压。

- **B200**：148 SM，192GB HBM3e。**GB202**：192 SM，24,576 FP32 Core，TSMC N4P。

- **LLM 性能：**Mistral-7B FP8 推理 78,400 tok/s（1.59x vs H200），FP4 达 112,800 tok/s。

---

---
id: arch-rubin
name: Rubin
year: 2026 (预计)
tags: R100, HBM4
---

### SM 配置
- SM (预计): 224
- Tensor Core 代: 6th [highlight]
- 晶体管: 3360 亿
- HBM4 (8 Stack): 288GB
- 显存带宽: 22 TB/s
- FP4 算力: 50 PF

### 说明
- **下一代数据中心平台，预计 2026 下半年。**

- **第 6 代 Tensor Core：**支持 FP4/FP6/FP8/FP16/BF16/TF32/FP32/FP64。**第 3 代 Transformer Engine**：硬件自适应压缩 + 跨层动态精度选择 + 双级微块缩放（NVFP4）。

- **HBM4 显存：**288GB，8 个堆叠，带宽 22 TB/s（Blackwell 的 2.8 倍）。

- **NVLink 6：**每 GPU 双向 3.6 TB/s（NVLink 5 的 2 倍）。

- **FP4 算力：**50 PFLOPS（Blackwell 20 PFLOPS 的 2.5 倍）。

- **Vera Rubin NVL72 系统：**72 GPU 聚合 FP4 推理 3,600 PFLOPS，NVLink 聚合带宽 260 TB/s。

TDP 1,800-2,300W。

---

## SM 结构演进对比

| 架构 | 年份 | SM 名称 | CUDA/FP32 | INT32 | FP64 | Tensor Core | Warp Sched. | Dispatch | LD/ST | SFU |
|------|------|---------|-----------|-------|------|-------------|-------------|----------|-------|-----|
| Fermi | 2010 | SM | 32 | 共享 | 共享 | - | 2 | 2 | 16 | 4 |
| Kepler | 2012 | SMX | 192 | 共享 | 64 | - | 4 | 8 | 32 | 32 |
| Maxwell | 2014 | SMM | 128 | 共享 | - | - | 4 | 8 | 32 | 32 |
| Pascal | 2016 | SM | 64 | 共享 | 32 | - | 2 | 4 | 16 | 16 |
| Volta | 2017 | SM | 64 | 64 | 32 | 8 (1th) | 4 | 4 | 32 | 16 |
| Turing | 2018 | SM | 64 | 64 | - | 8 (2th) | 4 | 4 | 16 | 16 |
| Ampere | 2020 | SM | 64 | 64 | 32 | 4 (3th) | 4| 4 | 32 | 16 |
| Ada | 2022 | SM | 128 | 64 | 2 | 4 (4th) | 4 | 4 | 32 | 16 |
| Hopper | 2022 | SM | 128 | 64 | 64 | 4 (4th) | 4 | 4 | 32 | 16 |
| Blackwell | 2024 | SM | 128 | 128 | TBD | 4 (5th) | 4 | 4 | ~32 | ~16 |
| Rubin | 2026 | SM | ~128+ | TBD | TBD | TBD (6th) | TBD | TBD | TBD | TBD |
