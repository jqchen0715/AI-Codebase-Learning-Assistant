#!/usr/bin/env python3
"""Collect reproducible demo and evaluation metrics for this repository."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3})")
RETRY_RE = re.compile(r"=\s*[A-Za-z_]+\(\s*max_retries=(\d+),\s*wait=(\d+)\s*\)")


def iter_demo_markdown_files(docs_dir: Path):
    if not docs_dir.exists():
        return
    for demo_dir in docs_dir.iterdir():
        if demo_dir.is_dir():
            yield from demo_dir.rglob("*.md")


def count_markdown_files(docs_dir: Path) -> int:
    return sum(1 for _ in iter_demo_markdown_files(docs_dir))


def count_chapter_files(docs_dir: Path) -> int:
    return sum(
        1
        for file_path in iter_demo_markdown_files(docs_dir)
        if file_path.name != "index.md"
    )


def collect_demo_repos(docs_dir: Path) -> list[str]:
    if not docs_dir.exists():
        return []
    return sorted(path.name for path in docs_dir.iterdir() if path.is_dir())


def collect_output_assets(output_root: Path) -> dict[str, object]:
    if not output_root.exists():
        return {
            "path": str(output_root),
            "markdown_files": 0,
            "key_assets_present": 0,
            "key_assets_expected": 4,
            "chapter_files": 0,
        }

    key_assets = {
        "index.md",
        "code_reading_route.md",
        "interview_qa.md",
        "project_mastery_report.md",
    }
    markdown_files = sorted(file_path.name for file_path in output_root.glob("*.md"))
    present_key_assets = sorted(asset for asset in key_assets if (output_root / asset).exists())

    return {
        "path": str(output_root),
        "markdown_files": len(markdown_files),
        "key_assets_present": len(present_key_assets),
        "key_assets_expected": len(key_assets),
        "chapter_files": len([name for name in markdown_files if name not in key_assets]),
        "present_key_assets": present_key_assets,
    }


def collect_log_window(log_file: Path) -> dict[str, object]:
    timestamps: list[datetime] = []
    if log_file.exists():
        for line in log_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = TIMESTAMP_RE.match(line)
            if match:
                timestamps.append(
                    datetime.strptime(
                        f"{match.group(1)}.{match.group(2)}",
                        "%Y-%m-%d %H:%M:%S.%f",
                    )
                )

    if not timestamps:
        return {
            "path": str(log_file),
            "timestamp_lines": 0,
            "start": None,
            "end": None,
            "duration_seconds": None,
            "duration_human": None,
        }

    duration_seconds = int((timestamps[-1] - timestamps[0]).total_seconds())
    minutes, seconds = divmod(duration_seconds, 60)
    return {
        "path": str(log_file),
        "timestamp_lines": len(timestamps),
        "start": timestamps[0].isoformat(sep=" "),
        "end": timestamps[-1].isoformat(sep=" "),
        "duration_seconds": duration_seconds,
        "duration_human": f"{minutes}m {seconds}s",
    }


def collect_retry_config(flow_file: Path) -> dict[str, object]:
    if not flow_file.exists():
        return {"llm_nodes_with_retry": 0, "unique_retry_configs": []}

    retry_configs = RETRY_RE.findall(flow_file.read_text(encoding="utf-8", errors="ignore"))
    unique_configs = sorted({(int(retries), int(wait)) for retries, wait in retry_configs})
    return {
        "llm_nodes_with_retry": len(retry_configs),
        "unique_retry_configs": [
            {"max_retries": retries, "wait_seconds": wait} for retries, wait in unique_configs
        ],
    }


def collect_metrics(repo_root: Path, log_file: Path, output_root: Path) -> dict[str, object]:
    docs_dir = repo_root / "docs"
    demo_repos = collect_demo_repos(docs_dir)
    output_assets = collect_output_assets(output_root)

    return {
        "repo_root": str(repo_root),
        "demo_repositories": {
            "count": len(demo_repos),
            "names": demo_repos,
        },
        "generated_docs": {
            "markdown_files": count_markdown_files(docs_dir),
            "chapter_files": count_chapter_files(docs_dir),
        },
        "self_analysis_demo": output_assets,
        "generation_time_sample": collect_log_window(log_file),
        "flow_success_proxy": {
            "main_flow_nodes_completed": 9 if output_assets["markdown_files"] else 0,
            "main_flow_nodes_expected": 9,
            "key_assets_success_rate": (
                f"{output_assets['key_assets_present']}/{output_assets['key_assets_expected']}"
            ),
        },
        "retry_mechanism": collect_retry_config(repo_root / "flow.py"),
        "quality_evaluation": {
            "implemented": "manual rubric documented in docs/evaluation.md",
            "automated_llm_quality_score": "not implemented yet",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect project demo/evaluation metrics.")
    parser.add_argument("--repo-root", default=".", help="Repository root directory.")
    parser.add_argument(
        "--log-file",
        default="logs/llm_calls_20260512.log",
        help="LLM log file used as the runtime sample.",
    )
    parser.add_argument(
        "--output-root",
        default="output/PocketFlow-Tutorial-Codebase-Knowledge#",
        help="Self-analysis demo output directory.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    log_file = (repo_root / args.log_file).resolve()
    output_root = (repo_root / args.output_root).resolve()
    metrics = collect_metrics(repo_root, log_file, output_root)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
