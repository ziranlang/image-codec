#!/usr/bin/env python3
"""Validate benchmark semantics as well as field presence. No third-party modules."""
import copy
import json
import math
from pathlib import Path
import re
import sys

REQUIRED = {"schema_version", "provider", "mode", "cache_policy", "timing_scope", "correctness_verified", "iterations",
            "p50_ns", "p95_ns", "total_ns", "input_bytes", "output_bytes", "pixels", "active_workers", "output_hash_algorithm",
            "output_hash", "samples_ns", "pixels_per_second", "cpu_ns_per_pixel", "peak_rss_bytes", "allocations", "energy_joules",
            "cpu_capabilities", "unavailable", "tool_versions"}
UNAVAILABLE = {"cpu_ns_per_pixel", "peak_rss_bytes", "allocations", "energy_joules", "cpu_capabilities"}

def validate(report):
    missing = REQUIRED - report.keys()
    if missing:
        raise ValueError(f"missing benchmark fields: {sorted(missing)}")
    if report.keys() - REQUIRED:
        raise ValueError("unknown benchmark fields outside schema 1")
    if report["schema_version"] != 1 or report["correctness_verified"] is not True or report["mode"] != "warm":
        raise ValueError("unsupported schema/mode or correctness unverified")
    for field in ("provider", "cache_policy", "timing_scope"):
        if not isinstance(report[field], str) or not report[field]:
            raise ValueError(f"missing {field}")
    for field in ("iterations", "p50_ns", "p95_ns", "total_ns", "input_bytes", "output_bytes", "pixels", "active_workers"):
        if type(report[field]) is not int or report[field] < 0:
            raise ValueError(f"invalid numeric field: {field}")
    if not 1 <= report["iterations"] <= 1024 or not 1 <= report["active_workers"] or min(report["input_bytes"], report["output_bytes"], report["pixels"]) <= 0:
        raise ValueError("empty benchmark")
    samples = report["samples_ns"]
    if not isinstance(samples, list) or len(samples) != report["iterations"] or any(type(v) is not int or v < 0 for v in samples):
        raise ValueError("invalid timing samples")
    samples = sorted(samples)
    if report["total_ns"] != sum(samples) or report["p50_ns"] != samples[math.ceil(len(samples) * .50) - 1] or report["p95_ns"] != samples[math.ceil(len(samples) * .95) - 1]:
        raise ValueError("percentiles/total disagree with measured samples")
    throughput = report["pixels_per_second"]
    if report["total_ns"] == 0:
        if throughput is not None:
            raise ValueError("zero timing must have unavailable throughput")
    else:
        expected = report["pixels"] * report["iterations"] * 1e9 / report["total_ns"]
        if type(throughput) is not int or abs(throughput - expected) > 1.1:
            raise ValueError("throughput disagrees with measured timing")
    if report["output_bytes"] != report["pixels"] * 4:
        raise ValueError("output is not tightly packed RGBA8")
    if report["output_hash_algorithm"] != "fnv1a64" or not re.fullmatch(r"[0-9a-f]{16}", report["output_hash"]):
        raise ValueError("invalid output hash")
    # Schema 1 has no instruments for these fields. Keep absence truthful.
    for field in UNAVAILABLE:
        if report[field] is not None or not isinstance(report["unavailable"].get(field), str) or not report["unavailable"][field]:
            raise ValueError(f"unavailable metric must be null with reason: {field}")
    versions = report["tool_versions"]
    if versions.keys() - {"runner", "ziran", "codec", "codec_revision"}:
        raise ValueError("unknown tool version fields outside schema 1")
    if not versions.get("runner") or "ziran" not in versions or versions["ziran"] is not None and not isinstance(versions["ziran"], str):
        raise ValueError("missing tool versions or explicit unavailable version")
    for field in ("codec", "codec_revision"):
        if field in versions and versions[field] is not None and (not isinstance(versions[field], str) or not versions[field]):
            raise ValueError(f"invalid optional tool version: {field}")
    return report

def self_test(report):
    schema = json.loads((Path(__file__).resolve().parents[1] / "docs/benchmark.schema.json").read_text())
    assert set(schema["required"]) == REQUIRED
    assert set(schema["properties"]) == REQUIRED
    for field in UNAVAILABLE:
        assert schema["properties"][field]["type"] == "null"
    for extra in ("root", "versions"):
        broken = copy.deepcopy(report)
        if extra == "root":
            broken["unknown_metric"] = 0
        else:
            broken["tool_versions"]["unknown_tool"] = 0
        try:
            validate(broken)
        except ValueError:
            continue
        raise AssertionError("closed schema accepted unknown fields")
    for field in REQUIRED:
        broken = copy.deepcopy(report)
        del broken[field]
        try:
            validate(broken)
        except (ValueError, KeyError, TypeError):
            continue
        raise AssertionError(f"missing field accepted: {field}")
    for field in UNAVAILABLE:
        broken = copy.deepcopy(report); broken[field] = 0
        try:
            validate(broken)
        except ValueError:
            continue
        raise AssertionError(f"invented metric accepted: {field}")
    broken = copy.deepcopy(report); broken["p95_ns"] += 1
    try:
        validate(broken)
    except ValueError:
        return
    raise AssertionError("invented percentile accepted")

if __name__ == "__main__":
    first, second = [validate(json.loads(Path(path).read_text())) for path in sys.argv[1:]]
    self_test(first)
    for field in ("output_hash", "pixels", "output_bytes", "input_bytes", "provider", "active_workers", "tool_versions"):
        assert first[field] == second[field], field
    print("Benchmark reports: real samples, strict hash, stable correctness, complete schema and truthful nulls verified")
