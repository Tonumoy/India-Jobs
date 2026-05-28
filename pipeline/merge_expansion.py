"""
Merge pipeline/expansion_data.py into data/occupations.json.

- Skips duplicates by slug
- Refuses to add an occupation whose sector isn't already in the file unless
  it's an explicitly new sector listed in NEW_SECTORS
- Updates meta.total_occupations and meta.total_workforce_covered
"""
from __future__ import annotations
import json
from pathlib import Path

from expansion_data import NEW_OCCUPATIONS

ROOT = Path(__file__).parent.parent
OCC_PATH = ROOT / "data" / "occupations.json"

NEW_SECTORS = {
    "Beauty & Personal Services",
    "Religious & Cultural Services",
    "Domestic & Personal Services",
    "Security Services",
    "Real Estate",
    "Sports & Athletics",
    "Social Services & NGO",
}


def main():
    bundle = json.loads(OCC_PATH.read_text(encoding="utf-8"))
    existing_slugs = {o["slug"] for o in bundle["occupations"]}
    existing_sectors = {o["sector"] for o in bundle["occupations"]}
    valid_sectors = existing_sectors | NEW_SECTORS

    added = 0
    skipped_dup = []
    skipped_bad_sector = []
    for occ in NEW_OCCUPATIONS:
        if occ["slug"] in existing_slugs:
            skipped_dup.append(occ["slug"])
            continue
        if occ["sector"] not in valid_sectors:
            skipped_bad_sector.append((occ["slug"], occ["sector"]))
            continue
        bundle["occupations"].append(occ)
        existing_slugs.add(occ["slug"])
        added += 1

    bundle["meta"]["total_occupations"] = len(bundle["occupations"])
    bundle["meta"]["total_workforce_covered"] = sum(o["value"] for o in bundle["occupations"])
    bundle["meta"]["last_updated"] = "2026-05-28"

    OCC_PATH.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Added {added} new occupations.")
    print(f"Total occupations: {bundle['meta']['total_occupations']}")
    print(f"Total workforce covered: {bundle['meta']['total_workforce_covered']:,}")
    if skipped_dup:
        print(f"Skipped {len(skipped_dup)} duplicates: {skipped_dup}")
    if skipped_bad_sector:
        print(f"Skipped {len(skipped_bad_sector)} for unknown sector: {skipped_bad_sector}")


if __name__ == "__main__":
    main()
