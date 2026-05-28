"""
Flatten the occupations master JSON into a CSV for spreadsheet exploration.

Output: data/occupations.csv
"""

from __future__ import annotations
import csv
import json
from pathlib import Path

from make_prompt import EDU_LABELS, HIRE_LABELS

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"


def main():
    with open(DATA_DIR / "occupations.json") as f:
        bundle = json.load(f)

    scores = {}
    scores_path = DATA_DIR / "scores.json"
    if scores_path.exists():
        scores = json.loads(scores_path.read_text(encoding="utf-8"))

    rows = []
    for occ in bundle["occupations"]:
        score = scores.get(occ["slug"], {})
        rows.append({
            "slug": occ["slug"],
            "name": occ["name"],
            "sector": occ["sector"],
            "employment": occ["value"],
            "employment_millions": round(occ["value"] / 1_000_000, 2),
            "median_pay_inr": occ["pay"],
            "median_pay_lakh": round(occ["pay"] / 100_000, 1),
            "education_code": occ["edu"],
            "education_label": EDU_LABELS[occ["edu"]],
            "hiring_trend_code": occ["hire"],
            "hiring_trend_label": HIRE_LABELS[occ["hire"]],
            "ai_exposure": score.get("score", ""),
            "ai_rationale": score.get("rationale", ""),
            "source": occ["source"],
        })

    out_path = DATA_DIR / "occupations.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
