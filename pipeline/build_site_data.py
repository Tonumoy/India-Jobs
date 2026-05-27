"""
Merge occupations master + LLM scores into a compact `site/data.json`
that the frontend treemap consumes.

Schema (kept minimal — keys are short for smaller JSON over the wire):
{
  "meta": {...},
  "sectors": [
    {
      "n": "Sector name",
      "ch": [
        { "n": "Occupation", "s": "slug", "v": value,
          "ai": ai_score, "h": hire, "p": pay, "e": edu,
          "src": "source citation", "r": "LLM rationale" },
        ...
      ]
    },
    ...
  ]
}

Usage:
  uv run python pipeline/build_site_data.py
"""

from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"


def main():
    with open(DATA_DIR / "occupations.json") as f:
        bundle = json.load(f)

    scores_path = DATA_DIR / "scores.json"
    if scores_path.exists():
        scores = json.loads(scores_path.read_text())
    else:
        scores = {}
        print("[warn] data/scores.json not found — AI exposure layer will be missing.")
        print("       Run `uv run python pipeline/score.py` first.")

    # Group occupations by sector, preserving insertion order from occupations.json
    by_sector: dict[str, list] = defaultdict(list)
    for occ in bundle["occupations"]:
        sc = scores.get(occ["slug"], {})
        by_sector[occ["sector"]].append({
            "n": occ["name"],
            "s": occ["slug"],
            "v": occ["value"],
            "ai": sc.get("score"),
            "h": occ["hire"],
            "p": occ["pay"],
            "e": occ["edu"],
            "src": occ["source"],
            "r": sc.get("rationale", ""),
        })

    site_data = {
        "meta": {
            "total_occupations": len(bundle["occupations"]),
            "total_sectors": len(by_sector),
            "total_workforce_covered": sum(o["value"] for o in bundle["occupations"]),
            "last_updated": bundle["meta"]["last_updated"],
            "scoring_model": next(iter(scores.values())).get("model", "n/a") if scores else "n/a",
            "edu_codes": bundle["meta"]["edu_codes"],
            "hire_codes": bundle["meta"]["hire_codes"],
        },
        "sectors": [
            {"n": name, "ch": occs}
            for name, occs in by_sector.items()
        ],
    }

    SITE_DIR.mkdir(exist_ok=True)
    out = SITE_DIR / "data.json"
    out.write_text(json.dumps(site_data, indent=2, ensure_ascii=False))
    print(f"Wrote {out} ({out.stat().st_size:,} bytes, {len(bundle['occupations'])} occupations).")


if __name__ == "__main__":
    main()
