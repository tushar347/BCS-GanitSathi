#!/usr/bin/env python3
"""Run the canonical local verification gate for GonitSathi.

The gate is intentionally stricter than a test-only command. A successful exit means all
checks implemented here passed in the repository's required Python environment. It does not
prove behavior that has no test or contract.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
CHECK_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str
    duration_seconds: float


def _run_check(name: str, check: Callable[[], str]) -> CheckResult:
    started = time.perf_counter()
    try:
        detail = check()
        passed = True
    except Exception as exc:  # Each phase must report without hiding later failures.
        detail = str(exc) or type(exc).__name__
        passed = False
    return CheckResult(name, passed, detail, time.perf_counter() - started)


def _expected_python() -> str:
    version_file = REPOSITORY_ROOT / ".python-version"
    if not version_file.is_file():
        raise RuntimeError("Missing .python-version")
    expected = version_file.read_text(encoding="utf-8").strip()
    if not expected:
        raise RuntimeError(".python-version is empty")
    return expected


def check_python_runtime() -> str:
    expected = _expected_python()
    actual = f"{sys.version_info.major}.{sys.version_info.minor}"
    if actual != expected:
        raise RuntimeError(
            f"requires Python {expected}.x, running {sys.version.split()[0]} from {sys.executable}"
        )
    return f"Python {sys.version.split()[0]} ({sys.executable})"


def check_dependencies() -> str:
    required_modules = {
        "numpy": "requirements.txt",
        "pydantic": "requirements.txt",
        "pytest": "requirements.txt",
        "ruff": "requirements-dev.txt",
        "psutil": "requirements.txt",
        "scipy": "requirements.txt",
        "sympy": "requirements.txt",
        "torch": "requirements.txt",
        "transformers": "requirements.txt",
        "yaml": "requirements-dev.txt",
    }
    missing = [
        f"{module} ({source})"
        for module, source in required_modules.items()
        if importlib.util.find_spec(module) is None
    ]
    if missing:
        raise RuntimeError(
            "missing modules: " + ", ".join(missing) + "; install requirements-dev.txt"
        )
    return f"{len(required_modules)} required modules available"


def _python_files() -> list[Path]:
    files: list[Path] = []
    for directory_name in ("src", "tests", "scripts"):
        directory = REPOSITORY_ROOT / directory_name
        if directory.is_dir():
            files.extend(directory.rglob("*.py"))
    return sorted(files)


def check_python_syntax() -> str:
    files = _python_files()
    if not files:
        raise RuntimeError("no Python files found under src, tests, or scripts")

    failures: list[str] = []
    for path in files:
        try:
            compile(path.read_bytes(), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"{path.relative_to(REPOSITORY_ROOT)}: {exc}")
    if failures:
        raise RuntimeError("syntax failures:\n" + "\n".join(failures))
    return f"compiled {len(files)} Python files in memory"


def check_contracts() -> str:
    try:
        import yaml
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError(f"contract dependency unavailable: {exc}") from exc

    config_root = REPOSITORY_ROOT / "configs"
    json_files = sorted(config_root.rglob("*.json"))
    yaml_files = sorted([*config_root.rglob("*.yaml"), *config_root.rglob("*.yml")])
    if not json_files or not yaml_files:
        raise RuntimeError("expected at least one JSON and one YAML configuration file")

    for path in json_files:
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
    for path in yaml_files:
        with path.open("r", encoding="utf-8") as handle:
            yaml.safe_load(handle)

    model_modules = (
        "src.controller.schemas",
        "src.controller.prompt_contracts",
        "src.benchmark.loader",
        "src.verifier.symbolic_verifier",
    )
    generated_models = 0
    for module_name in model_modules:
        module = importlib.import_module(module_name)
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, BaseModel)
                and value is not BaseModel
                and value.__module__ == module_name
            ):
                value.model_json_schema()
                generated_models += 1

    return (
        f"parsed {len(json_files)} JSON and {len(yaml_files)} YAML files; "
        f"generated {generated_models} Pydantic schemas"
    )


def _source_module_names() -> list[str]:
    names: set[str] = set()
    for path in SOURCE_ROOT.rglob("*.py"):
        relative = path.relative_to(REPOSITORY_ROOT).with_suffix("")
        parts = list(relative.parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            names.add(".".join(parts))
    return sorted(names)


def check_source_imports() -> str:
    module_names = _source_module_names()
    failures: list[str] = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")
    if failures:
        raise RuntimeError("source import failures:\n" + "\n".join(failures))
    return f"imported {len(module_names)} source modules"


def _run_process(arguments: list[str]) -> str:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT)
    completed = subprocess.run(
        arguments,
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=CHECK_TIMEOUT_SECONDS,
        check=False,
    )
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    if completed.returncode != 0:
        if len(output) > 12_000:
            output = output[-12_000:]
            output = "[output truncated to final 12000 characters]\n" + output
        raise RuntimeError(output or f"command exited with status {completed.returncode}")
    lines = output.splitlines()
    return lines[-1] if lines else "completed successfully"


def check_ruff() -> str:
    return _run_process(
        [sys.executable, "-m", "ruff", "check", "src", "tests", "scripts"]
    )


def check_pytest() -> str:
    return _run_process(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]
    )


def check_git_diff() -> str:
    return _run_process(["git", "diff", "--check"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the GonitSathi repository verification gate.")
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip pytest for a faster diagnostic run. A skipped run is not a full verification.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(REPOSITORY_ROOT)
    sys.path.insert(0, str(REPOSITORY_ROOT))
    sys.dont_write_bytecode = True

    checks: list[tuple[str, Callable[[], str]]] = [
        ("Python runtime", check_python_runtime),
        ("Dependencies", check_dependencies),
        ("Python syntax", check_python_syntax),
        ("Configuration and schemas", check_contracts),
        ("Source imports", check_source_imports),
        ("Ruff correctness", check_ruff),
        ("Git whitespace", check_git_diff),
    ]
    if not args.skip_tests:
        checks.append(("Pytest suite", check_pytest))

    print("GonitSathi repository verification")
    print(f"Repository: {REPOSITORY_ROOT}")
    results: list[CheckResult] = []
    for name, function in checks:
        result = _run_check(name, function)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"\n[{status}] {result.name} ({result.duration_seconds:.2f}s)")
        print(result.detail)

    failures = [result for result in results if not result.passed]
    print("\n" + "=" * 72)
    if failures:
        print(f"VERIFICATION FAILED: {len(failures)} of {len(results)} checks failed.")
        print("The repository must not be described as fully verified.")
        return 1
    if args.skip_tests:
        print("DIAGNOSTIC CHECKS PASSED, BUT TESTS WERE SKIPPED: not a full verification.")
        return 2
    print(f"VERIFICATION PASSED: all {len(results)} checks passed.")
    print("This certifies the implemented gate only; untested behavior is not guaranteed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

