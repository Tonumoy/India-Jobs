"""
Merge pipeline/expansion_data_v2.py into data/occupations.json. Same logic as
merge_expansion.py but with the v2 NEW_SECTORS allowlist.
"""
from __future__ import annotations
import json
from pathlib import Path

from expansion_data_v2 import NEW_OCCUPATIONS, NEW_SECTORS_V2

ROOT = Path(__file__).parent.parent
OCC_PATH = ROOT / "data" / "occupations.json"


def main():
    bundle = json.loads(OCC_PATH.read_text(encoding="utf-8"))
    existing_slugs = {o["slug"] for o in bundle["occupations"]}
    existing_sectors = {o["sector"] for o in bundle["occupations"]}
    valid_sectors = existing_sectors | NEW_SECTORS_V2

    added, dup, bad_sec = 0, [], []
    for occ in NEW_OCCUPATIONS:
        if occ["slug"] in existing_slugs:
            dup.append(occ["slug"]); continue
        if occ["sector"] not in valid_sectors:
            bad_sec.append((occ["slug"], occ["sector"])); continue
        bundle["occupations"].append(occ)
        existing_slugs.add(occ["slug"]); added += 1

    bundle["meta"]["total_occupations"] = len(bundle["occupations"])
    bundle["meta"]["total_workforce_covered"] = sum(o["value"] for o in bundle["occupations"])
    bundle["meta"]["total_sectors"] = len(set(o["sector"] for o in bundle["occupations"]))
    bundle["meta"]["last_updated"] = "2026-05-29"

    OCC_PATH.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Added {added} new occupations across {len(NEW_SECTORS_V2)} new sectors.")
    print(f"Total occupations: {bundle['meta']['total_occupations']}")
    print(f"Total sectors:     {bundle['meta']['total_sectors']}")
    print(f"Total workforce:   {bundle['meta']['total_workforce_covered']:,}")
    if dup: print(f"Skipped {len(dup)} duplicates: {dup}")
    if bad_sec: print(f"Skipped {len(bad_sec)} for bad sector: {bad_sec}")


if __name__ == "__main__":
    main()
