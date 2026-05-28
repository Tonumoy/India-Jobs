"""
Phase C cleanup: adjust aggregate categories so the new granular occupations
don't double-count their workers.

When the expansion split a large aggregate into specific trades (e.g. the
50M 'construction-labour' bucket into masons/carpenters/electricians/etc.),
we reduce the aggregate to represent only the residual general / unskilled
fraction. The granular trades together with the (smaller) aggregate now
sum to approximately the original number.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
OCC_PATH = ROOT / "data" / "occupations.json"

# slug -> (new_value, new_name_if_renamed_else_None, note)
ADJUSTMENTS = {
    # Construction granular trades now account for ~35M of the original 50M.
    # The residual represents general / unskilled construction labour.
    "construction-labour": (12000000, "Construction labour (general / unskilled)",
        "Reduced from 50M to 12M after adding 10 specific construction trades."),
    # Garment workers (5M) split out of the textile aggregate (12M).
    "textile-workers": (5000000, "Textile workers (yarn, fabric, weaving)",
        "Reduced from 12M to 5M after splitting out garment-workers."),
    # Auto-drivers (5.5M) split out of the combined cab/auto bucket.
    "cab-drivers": (1500000, "Taxi & cab drivers",
        "Reduced from 5.5M to 1.5M after splitting out auto-rickshaw drivers."),
    # 'Delivery' was 3M but is fully replaced by food-delivery (1.5M),
    # ecommerce-delivery (1.3M), bike-taxi (0.95M) and traditional courier.
    # Keep it as the residual non-platform last-mile delivery channel.
    "delivery": (250000, "Last-mile delivery (non-platform / courier)",
        "Reduced from 3M to 250K after splitting out platform-based delivery roles."),
    # Surgeons (165K) and dentists/AYUSH/mental-health are now separate.
    # 'doctors' represents allopathic non-surgical practitioners.
    "doctors": (1100000, "Doctors (general practitioners, physicians)",
        "Reduced from 1.3M to 1.1M after splitting out surgeons; dentists/AYUSH already excluded."),
    # ASHA (1.05M) and Anganwadi (2.7M) are now separate front-line categories.
    "govt-clerical": (1200000, "Government clerical & admin staff",
        "Reduced from 4.5M to 1.2M after splitting out ASHA/Anganwadi/Municipal workers as separate lines."),
    # ASHA workers are state community health front-line; reduce govt-healthcare.
    "govt-healthcare": (900000, "Healthcare staff (govt) — doctors, nurses, paramedics",
        "Reduced from 1.8M to 0.9M after ASHA workers became a separate line."),
}


def main():
    bundle = json.loads(OCC_PATH.read_text(encoding="utf-8"))
    changes = []
    by_slug = {o["slug"]: o for o in bundle["occupations"]}
    for slug, (new_val, new_name, note) in ADJUSTMENTS.items():
        if slug not in by_slug:
            print(f"[warn] {slug} not found, skipping")
            continue
        old_val = by_slug[slug]["value"]
        by_slug[slug]["value"] = new_val
        if new_name:
            by_slug[slug]["name"] = new_name
        changes.append((slug, old_val, new_val, note))

    # Update meta.
    bundle["meta"]["total_workforce_covered"] = sum(o["value"] for o in bundle["occupations"])
    OCC_PATH.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")

    for slug, old, new, note in changes:
        delta = old - new
        print(f"  {slug:25} {old:>11,} -> {new:>11,}  (-{delta:,})")
        print(f"    {note}")
    print(f"\nNew total workforce covered: {bundle['meta']['total_workforce_covered']:,}")
    print(f"Total occupations: {len(bundle['occupations'])}")


if __name__ == "__main__":
    main()
