"""Tests for hardware and pilot profiling module (Task 3.5)."""

import json
from pathlib import Path

from src.evaluation.profiler import collect_hardware_spec, compute_percentiles, run_full_profiling


def test_collect_hardware_spec():
    hw = collect_hardware_spec()
    assert hw.platform_system in ["Linux", "Darwin", "Windows"]
    assert hw.cpu_physical_cores >= 1
    assert hw.total_ram_bytes > 0
    assert hw.python_version != ""


def test_compute_percentiles():
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = compute_percentiles(data)
    assert res["p50"] == 30.0
    assert res["min"] == 10.0
    assert res["max"] == 50.0
    assert res["avg"] == 30.0

    empty = compute_percentiles([])
    assert empty["p50"] == 0.0


def test_run_full_profiling(tmp_path: Path):
    out_dir = str(tmp_path / "test_prof")
    payload = run_full_profiling(max_families=1, output_dir=out_dir)

    assert "hardware_spec" in payload
    assert "profiles" in payload
    assert "GonitSathi_G" in payload["profiles"]
    assert "B0_RuleTemplate" in payload["profiles"]

    json_file = Path(out_dir) / "hardware_profile.json"
    assert json_file.exists()
    with open(json_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["total_families_profiled"] == 1
