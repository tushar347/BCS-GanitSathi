"""Pipeline latency profiler and hardware/resource profiling utility for GonitSathi.

Instruments each stage of the process_student_step pipeline to measure
per-component latency (normalize -> verify -> admit -> belief_update -> probe_select -> guardrail).
Also provides system-wide host hardware profiling and token/call profiling across all 8 tutoring systems
(B0-B6 + G) in compliance with OE-Agent @ ACML 2026 standards (Task 3.5).
"""

from __future__ import annotations

import json
import math
import os
import platform
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:
    psutil = None

from src.baselines.b0_rule_template import RuleTemplateTutor
from src.baselines.b1_prompted import PromptedTutor
from src.baselines.b2_verify_then_generate import VerifyThenGenerateTutor
from src.baselines.b3_bayesian import BayesianDiagnosticTutor
from src.baselines.b4_intellicode import IntelliCodeTutor
from src.baselines.b5_scaffoldlm import ScaffoldLMTutor
from src.baselines.b6_slow import SlowWorkspaceTutor
from src.baselines.gonitsathi_adapter import GonitSathiTutor
from src.benchmark.dataset_ingester import BCSDatasetIngester
from src.controller.schemas import AssistanceLevel


@dataclass
class StageTimingRecord:
    """Timing record for a single pipeline stage."""
    stage_name: str
    start_time: float
    end_time: float

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000


@dataclass
class StepProfile:
    """Complete timing profile for one process_student_step call."""
    step_index: int
    family_id: str
    item_id: str
    total_start: float = 0.0
    total_end: float = 0.0
    stage_timings: List[StageTimingRecord] = field(default_factory=list)

    @property
    def total_ms(self) -> float:
        return (self.total_end - self.total_start) * 1000

    def to_dict(self) -> Dict[str, Any]:
        stages = {s.stage_name: round(s.duration_ms, 3) for s in self.stage_timings}
        return {
            "step_index": self.step_index,
            "family_id": self.family_id,
            "item_id": self.item_id,
            "total_ms": round(self.total_ms, 3),
            "stages_ms": stages,
        }


class PipelineProfiler:
    """Collects timing profiles across multiple pipeline invocations."""

    def __init__(self):
        self.profiles: List[StepProfile] = []
        self._current_profile: Optional[StepProfile] = None
        self._stage_start: float = 0.0

    def begin_step(self, step_index: int, family_id: str, item_id: str) -> None:
        """Begin timing a new pipeline step."""
        self._current_profile = StepProfile(
            step_index=step_index,
            family_id=family_id,
            item_id=item_id,
            total_start=time.perf_counter(),
        )

    def begin_stage(self, stage_name: str) -> None:
        """Begin timing a pipeline stage."""
        self._stage_start = time.perf_counter()

    def end_stage(self, stage_name: str) -> None:
        """End timing a pipeline stage and record it."""
        if self._current_profile is not None:
            self._current_profile.stage_timings.append(
                StageTimingRecord(
                    stage_name=stage_name,
                    start_time=self._stage_start,
                    end_time=time.perf_counter(),
                )
            )

    def end_step(self) -> Optional[StepProfile]:
        """End timing the current step. Returns the completed profile."""
        if self._current_profile is not None:
            self._current_profile.total_end = time.perf_counter()
            self.profiles.append(self._current_profile)
            result = self._current_profile
            self._current_profile = None
            return result
        return None

    def get_summary(self) -> Dict[str, Any]:
        """Generate an aggregate summary of all profiled steps."""
        if not self.profiles:
            return {"total_steps": 0}

        total_steps = len(self.profiles)
        total_times = [p.total_ms for p in self.profiles]
        avg_total = sum(total_times) / total_steps
        max_total = max(total_times)
        min_total = min(total_times)
        p95_total = sorted(total_times)[int(0.95 * total_steps)] if total_steps > 1 else total_times[0]

        # Per-stage aggregation
        stage_times: Dict[str, List[float]] = {}
        for p in self.profiles:
            for s in p.stage_timings:
                if s.stage_name not in stage_times:
                    stage_times[s.stage_name] = []
                stage_times[s.stage_name].append(s.duration_ms)

        stage_summary = {}
        for stage_name, times in stage_times.items():
            stage_summary[stage_name] = {
                "count": len(times),
                "avg_ms": round(sum(times) / len(times), 3),
                "max_ms": round(max(times), 3),
                "min_ms": round(min(times), 3),
                "total_ms": round(sum(times), 3),
            }

        return {
            "total_steps": total_steps,
            "total_latency": {
                "avg_ms": round(avg_total, 3),
                "max_ms": round(max_total, 3),
                "min_ms": round(min_total, 3),
                "p95_ms": round(p95_total, 3),
            },
            "per_stage": stage_summary,
        }

    def get_per_step_report(self) -> List[Dict[str, Any]]:
        """Return a per-step timing report."""
        return [p.to_dict() for p in self.profiles]


@dataclass
class HardwareSpecification:
    """Detailed host hardware and environment profile."""
    platform_system: str
    platform_release: str
    platform_version: str
    machine_arch: str
    python_version: str
    python_compiler: str
    cpu_model: str
    cpu_physical_cores: int
    cpu_logical_cores: int
    cpu_max_mhz: float
    total_ram_bytes: int
    total_ram_gb: float
    gpu_name: Optional[str] = None
    gpu_memory_mb: Optional[int] = None
    gpu_driver_version: Optional[str] = None


@dataclass
class ProfilingResult:
    """Performance and resource consumption profile for a tutoring system."""
    system_name: str
    total_steps: int
    latencies_ms: List[float] = field(default_factory=list)
    p50_latency_ms: float = 0.0
    p90_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    total_tokens_generated: int = 0
    avg_tokens_per_step: float = 0.0
    total_neural_calls: int = 0
    total_symbolic_calls: int = 0
    memory_peak_mb: float = 0.0


def collect_hardware_spec() -> HardwareSpecification:
    """Collect host hardware and OS specifications."""
    if psutil is not None:
        vm_total = psutil.virtual_memory().total
        phys_cores = psutil.cpu_count(logical=False) or 1
        log_cores = psutil.cpu_count(logical=True) or 1
        cpu_freq = psutil.cpu_freq()
        max_mhz = cpu_freq.max if cpu_freq else 0.0
    else:
        vm_total = 16 * (1024**3)  # default estimate
        phys_cores = os.cpu_count() or 1
        log_cores = os.cpu_count() or 1
        max_mhz = 0.0

    cpu_model = "Unknown CPU"
    try:
        if platform.system() == "Linux" and os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        cpu_model = line.split(":", 1)[1].strip()
                        break
        else:
            cpu_model = platform.processor() or "Unknown CPU"
    except Exception:
        cpu_model = platform.processor() or "Unknown CPU"

    gpu_name: Optional[str] = None
    gpu_mem: Optional[int] = None
    gpu_driver: Optional[str] = None
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = [p.strip() for p in res.stdout.strip().split(",")]
            if len(parts) >= 3:
                gpu_name = parts[0]
                mem_str = parts[1].replace("MiB", "").strip()
                gpu_mem = int(mem_str) if mem_str.isdigit() else None
                gpu_driver = parts[2]
    except Exception:
        pass

    return HardwareSpecification(
        platform_system=platform.system(),
        platform_release=platform.release(),
        platform_version=platform.version(),
        machine_arch=platform.machine(),
        python_version=platform.python_version(),
        python_compiler=platform.python_compiler(),
        cpu_model=cpu_model,
        cpu_physical_cores=phys_cores,
        cpu_logical_cores=log_cores,
        cpu_max_mhz=max_mhz,
        total_ram_bytes=vm_total,
        total_ram_gb=round(vm_total / (1024**3), 2),
        gpu_name=gpu_name,
        gpu_memory_mb=gpu_mem,
        gpu_driver_version=gpu_driver,
    )


def compute_percentiles(values: List[float]) -> Dict[str, float]:
    """Compute p50, p90, p95 from a float sequence."""
    if not values:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}
    sorted_v = sorted(values)
    n = len(sorted_v)

    def _get_pct(p: float) -> float:
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_v[int(k)]
        d0 = sorted_v[int(f)] * (c - k)
        d1 = sorted_v[int(c)] * (k - f)
        return d0 + d1

    return {
        "p50": round(_get_pct(50), 2),
        "p90": round(_get_pct(90), 2),
        "p95": round(_get_pct(95), 2),
        "avg": round(sum(sorted_v) / n, 2),
        "min": round(sorted_v[0], 2),
        "max": round(sorted_v[-1], 2),
    }


def profile_system(
    system: Any,
    dataset_families: list,
    ingester: BCSDatasetIngester,
) -> ProfilingResult:
    """Profile a single tutor system across benchmark families."""
    process = psutil.Process(os.getpid()) if psutil is not None else None
    latencies: List[float] = []
    total_tokens = 0
    total_neural = 0
    total_symbolic = 0
    peak_mem_mb = 0.0

    for family in dataset_families:
        dag = ingester.build_problem_dag(family.item_id)
        if dag is None:
            continue
        for history in family.attempt_histories:
            system.reset(learner_id=f"prof_{history.history_id}", problem_dag=dag)
            for event in history.events:
                raw_text = event.get("text", "")
                assistance = AssistanceLevel(event.get("assistance_level", "none"))
                group_id = event.get("independent_evidence_group")

                t0 = time.perf_counter()
                step_res = system.process_student_step(
                    raw_text=raw_text,
                    problem_dag=dag,
                    assistance_level=assistance,
                    independent_group_id=group_id,
                )
                wall_ms = (time.perf_counter() - t0) * 1000.0

                measured_lat = step_res.latency_ms if step_res.latency_ms > 0 else wall_ms
                latencies.append(measured_lat)

                total_tokens += step_res.tokens_generated
                total_neural += step_res.neural_calls
                total_symbolic += step_res.symbolic_calls

                if process is not None:
                    mem_mb = process.memory_info().rss / (1024 * 1024)
                    if mem_mb > peak_mem_mb:
                        peak_mem_mb = mem_mb

    stats = compute_percentiles(latencies)
    total_steps = len(latencies)

    return ProfilingResult(
        system_name=system.name,
        total_steps=total_steps,
        latencies_ms=[round(x, 2) for x in latencies],
        p50_latency_ms=stats["p50"],
        p90_latency_ms=stats["p90"],
        p95_latency_ms=stats["p95"],
        avg_latency_ms=stats["avg"],
        min_latency_ms=stats["min"],
        max_latency_ms=stats["max"],
        total_tokens_generated=total_tokens,
        avg_tokens_per_step=round(total_tokens / max(1, total_steps), 2),
        total_neural_calls=total_neural,
        total_symbolic_calls=total_symbolic,
        memory_peak_mb=round(peak_mem_mb, 2),
    )


def run_full_profiling(
    max_families: int = 5,
    output_dir: str = "evaluations/profiling",
) -> Dict[str, Any]:
    """Profile all 8 systems (B0-B6, G) and host hardware."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    hw_spec = collect_hardware_spec()

    ingester = BCSDatasetIngester()
    ingester.load_all()
    dataset = ingester.build_benchmark_dataset(split="dev")
    families = dataset.families[:max_families]

    systems = [
        RuleTemplateTutor(),
        PromptedTutor(),
        VerifyThenGenerateTutor(),
        BayesianDiagnosticTutor(activation_threshold=0.80),
        IntelliCodeTutor(),
        ScaffoldLMTutor(),
        SlowWorkspaceTutor(),
        GonitSathiTutor(activation_threshold=0.80),
    ]

    profiles: Dict[str, Any] = {}
    for sys_obj in systems:
        prof = profile_system(sys_obj, families, ingester)
        profiles[sys_obj.name] = asdict(prof)

    payload = {
        "hardware_spec": asdict(hw_spec),
        "total_families_profiled": len(families),
        "split": dataset.split,
        "profiles": profiles,
    }

    json_file = out_path / "hardware_profile.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload
