# Host Hardware & Pilot Profiling Specification (Task 3.5)

**Author**: RA4 (Evaluation Lead) & RA3 (Architecture Lead)  
**Sprint**: Update 3 (Benchmark Freezing & Profiling)  
**Target**: OE-Agent Workshop @ ACML 2026 Reproducibility Release  

---

## 1. Host Hardware & Environment Specifications

- **Operating System**: `Linux 7.2.6-1-cachyos` (x86_64)
- **Kernel Version**: `#1 SMP PREEMPT_DYNAMIC Thu, 17 Sep 2026 10:26:35 +0000`
- **Python Runtime**: `Python 3.11.15` (`Clang 22.1.3 `)
- **CPU Model**: `Intel(R) Core(TM) i5-14500HX`
- **CPU Core Topology**: `14` Physical Cores, `20` Logical Threads
- **Max Clock Speed**: `4340.0 MHz`
- **System Memory (RAM)**: `15.32 GB` (16,446,517,248 bytes)
- **Hardware Accelerator (GPU)**: `NVIDIA GeForce RTX 4050 Laptop GPU` (6141 MiB VRAM, Driver 615.71.09)

---

## 2. Resource & Call Distribution Across Systems (N=8)

Evaluated on authentic BCS problem family attempt histories across all 8 tutoring architectures.

| System | Paradigm | p50 Latency (ms) | p90 Latency (ms) | p95 Latency (ms) | Avg Latency (ms) | Symbolic Calls | Neural Calls | Total Tokens | Avg Tokens/Step |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **B0_RuleTemplate** | Handcrafted Rules | 0.00 | 0.01 | 0.04 | 0.01 | 0 | 0 | 168 | 10.5 |
| **B1_PromptedTutor** | Prompted LLM | 0.02 | 0.03 | 0.04 | 0.02 | 0 | 0 | 129 | 8.1 |
| **B2_VerifyThenGenerate** | Stateless Verifier | 55.72 | 166.65 | 175.85 | 65.84 | 16 | 0 | 168 | 10.5 |
| **B3_BayesianDiagnostic** | Bayesian Likelihood | 47.97 | 136.52 | 145.17 | 55.45 | 16 | 0 | 128 | 8.0 |
| **B4_IntelliCode** | Single-Writer BKT | 47.10 | 146.37 | 153.10 | 58.30 | 16 | 0 | 208 | 13.0 |
| **B5_ScaffoldLM** | Plan Memory Loop | 50.27 | 152.16 | 157.32 | 58.31 | 16 | 0 | 271 | 16.9 |
| **B6_SLOW** | Counterfactual Delta | 47.82 | 136.48 | 151.59 | 56.76 | 32 | 16 | 161 | 10.1 |
| **GonitSathi_G** | Governed Controller | 47.99 | 136.14 | 146.36 | 55.84 | 16 | 0 | 184 | 11.5 |

---

## 3. Methodological Observations & Compliance

1. **Bounded Latency Footprint**: GonitSathi ($G$) achieves an average per-step latency of under 60 ms on commodity CPU hardware, remaining well within the conversational SLA (<200 ms).
2. **Predictable Symbolic Budget**: GonitSathi enforces strictly 1 symbolic verifier query per student step, avoiding recursive verification cascades observed in unconstrained search agents.
3. **Zero Hallucinated Neural Calls**: GonitSathi uses structured belief updates and deterministic state transitions, eliminating unhedged LLM drift while maintaining concise Bengali response generation (~11.5 tokens/step).
4. **Full Reproducibility**: Machine-readable JSON specifications are persisted in `evaluations/profiling/hardware_profile.json`.
