"""Pencatatan hasil uji usability. Hanya mencatat data nyata; tidak ada hasil bawaan."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass
class UsabilityResult:
    participant_id: str
    task: str
    completed: bool
    time_seconds: float
    errors: int
    notes: str = ""


def record_result(results: list[UsabilityResult], result: UsabilityResult) -> list[UsabilityResult]:
    results.append(result)
    return results


def compute_summary(results: list[UsabilityResult]) -> dict[str, Any]:
    """Ringkasan per tugas dan keseluruhan. Menyertakan jumlah peserta agar tidak digeneralisasi."""
    if not results:
        return {"total_participants": 0, "total_attempts": 0}
    participants = {r.participant_id for r in results}
    done = [r for r in results if r.completed]
    return {
        "total_participants": len(participants),
        "total_attempts": len(results),
        "task_completion_rate_pct": round(len(done) / len(results) * 100, 1),
        "average_time_seconds": round(sum(r.time_seconds for r in results) / len(results), 1),
        "average_time_completed_seconds": round(sum(r.time_seconds for r in done) / len(done), 1) if done else None,
        "total_errors": sum(r.errors for r in results),
    }


def save_results(results: list[UsabilityResult], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[f.name for f in fields(UsabilityResult)])
        writer.writeheader()
        writer.writerows(asdict(r) for r in results)


def load_results(path: str | Path) -> list[UsabilityResult]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            UsabilityResult(
                row["participant_id"], row["task"], row["completed"] == "True",
                float(row["time_seconds"]), int(row["errors"]), row.get("notes", ""),
            )
            for row in csv.DictReader(handle)
        ]
