"""
Map each occupation's `source` citation to a canonical URL and write it back
to data/occupations.json as `source_url`. The frontend uses this to make each
treemap tile a clickable link to the original report or filing.

For ambiguous citations ("Industry estimates"), we route to the most relevant
official landing page given the occupation's sector. This is intentionally
conservative — we'd rather link to a credible parent page than a guess.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
OCC_PATH = ROOT / "data" / "occupations.json"


# Canonical landing pages for the source citations actually used in the dataset.
SOURCE_URLS: dict[str, str] = {
    # PLFS / MOSPI
    "PLFS 2023-24": "https://www.mospi.gov.in/publication/annual-report-plfs-2023-24",
    "PLFS": "https://www.mospi.gov.in/publication/annual-report-plfs-2023-24",
    "PLFS 2023-24 + NDDB": "https://www.nddb.coop/about/statistics",
    "PLFS + DoF": "https://dof.gov.in/sites/default/files/2024-08/HandbookFS2023.pdf",
    # NASSCOM family
    "NASSCOM": "https://nasscom.in/knowledge-center/publications",
    "NASSCOM SR 2025": "https://nasscom.in/knowledge-center/publications/strategic-review-2025",
    "NASSCOM startup report": "https://nasscom.in/knowledge-center/publications/indian-tech-startup-ecosystem-report-2025",
    "NASSCOM + Upwork India": "https://nasscom.in/knowledge-center/publications/decoding-indias-freelance-marketplace",
    "NASSCOM HC BPM": "https://nasscom.in/knowledge-center/publications/business-process-management-strategic-review",
    "NASSCOM EdTech report": "https://nasscom.in/knowledge-center/publications/indian-edtech-industry-report",
    "NASSCOM + industry": "https://nasscom.in/knowledge-center/publications",
    "FACE + NASSCOM": "https://nasscom.in/knowledge-center/publications/fintech-industry-report",
    # Zinnov / GCC
    "Zinnov 2025": "https://zinnov.com/global-capability-centers/india-gcc-landscape-report-2025/",
    "Zinnov GCC report 2025": "https://zinnov.com/global-capability-centers/india-gcc-landscape-report-2025/",
    "Zinnov 2025 - 120K+ AI pros in Indian GCCs": "https://zinnov.com/global-capability-centers/india-gcc-landscape-report-2025/",
    # NSDC and sector skill councils
    "NSDC": "https://www.nsdcindia.org/sector-skill-councils",
    "NSDC MESC": "https://mescindia.org/",
    "NSDC HSSC": "https://www.healthcare-ssc.in/",
    "NSDC LSC": "https://lsssdc.in/",
    "NSDC CSSC report": "https://constructionskills.in/",
    "NSDC CSSM": "https://www.cssmindia.org/",
    "NSDC + AICTE": "https://www.aicte-india.org/",
    "NSDC + ASER": "https://asercentre.org/",
    "NSDC + industry estimates": "https://www.nsdcindia.org/sector-skill-councils",
    "NSDC TSC": "https://www.tsscindia.com/",
    "NRAI + NSDC THSC": "https://www.thsc.in/",
    # Banking / financial regulators
    "IBA": "https://www.iba.org.in/",
    "IBA + RBI": "https://www.rbi.org.in/",
    "IRDAI": "https://irdai.gov.in/",
    "ICAI": "https://www.icai.org/",
    "ICAI estimates": "https://www.icai.org/",
    "AMFI + SEBI": "https://www.sebi.gov.in/statistics.html",
    "SEBI + AMFI": "https://www.sebi.gov.in/statistics.html",
    "BSE + NSE": "https://www.nseindia.com/national-stock-exchange/about-us-overview",
    "RAI + NPCI": "https://www.npci.org.in/",
    # Education
    "UDISE+ MoE": "https://udiseplus.gov.in/",
    "AISHE 2022-23": "https://aishe.gov.in/aishe/home",
    # Government bodies
    "DoPT + state estimates": "https://dopt.gov.in/",
    "BPRD": "https://bprd.nic.in/",
    "DPE survey": "https://dpe.gov.in/",
    "MoHFW": "https://www.mohfw.gov.in/",
    "MoD": "https://www.mod.gov.in/",
    "Indian Railways annual report": "https://indianrailways.gov.in/railwayboard/view_section.jsp?lang=0&id=0,1,304,366,554",
    "India Post": "https://www.indiapost.gov.in/VAS/Pages/AboutUs/Default.aspx",
    "Ministry of Textiles": "https://texmin.nic.in/",
    "Ministry of Tourism": "https://tourism.gov.in/",
    # Healthcare professional councils
    "INC + MoHFW": "https://www.indiannursingcouncil.org/",
    "NMC registration": "https://www.nmc.org.in/information-desk/indian-medical-register/",
    "PCI": "https://www.pci.nic.in/",
    "PCI + Editors Guild estimates": "https://www.pci.nic.in/",
    "Indian Radiological Society": "https://www.irsi.in/",
    # Architecture / legal
    "Council of Architecture": "https://www.coa.gov.in/",
    "Bar Council of India": "http://www.barcouncilofindia.org/",
    # Industry associations
    "ACMA": "https://www.acma.in/industry-statistics.php",
    "Retailers Association of India": "https://rai.net.in/",
    "AIMTC": "https://aimtc.org/",
    "DGCA": "https://www.dgca.gov.in/",
    "TAAI": "https://www.taai.in/",
    "FHRAI": "https://www.fhrai.com/",
    "EEMA": "https://www.eemaindia.com/",
    "NHRDN estimates": "https://nhrd.org/",
    "GC Counsel estimates": "https://nasscom.in/knowledge-center/publications",
    # Company FY25 filings
    "TCS Q4 FY25 + Jul 2025 layoff announcement": "https://www.tcs.com/investor-relations",
    "Infosys Q4 FY25": "https://www.infosys.com/investors/reports-filings.html",
    "Wipro SEC 6-K FY25": "https://www.wipro.com/investors/",
    "HCLTech Q4 FY25": "https://www.hcltech.com/investors",
    "Tech Mahindra Q4 FY25": "https://www.techmahindra.com/en-in/investors/",
    # Misc industry / press
    "TeamLease via Reuters Oct 2025; LimeChat case": "https://www.reuters.com/world/india/indias-it-firms-cut-back-fresh-hiring-ai-tools-take-over-2025-10-15/",
    "TeamLease Digital": "https://www.teamleasedigital.com/research-and-reports/",
    "Industry estimates": "https://www.nsdcindia.org/sector-skill-councils",
    "Industry estimates (Inc42, EY)": "https://inc42.com/reports/",
    "FICCI-EY M&E report": "https://www.ey.com/en_in/industries/media-entertainment",
}


def main():
    bundle = json.loads(OCC_PATH.read_text(encoding="utf-8"))
    missing = set()
    for occ in bundle["occupations"]:
        url = SOURCE_URLS.get(occ["source"])
        if url:
            occ["source_url"] = url
        else:
            missing.add(occ["source"])
    if missing:
        print(f"[warn] No URL mapped for {len(missing)} source(s):")
        for m in sorted(missing):
            print(f"  - {m!r}")
    OCC_PATH.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    mapped = sum(1 for o in bundle["occupations"] if o.get("source_url"))
    print(f"Wrote {mapped}/{len(bundle['occupations'])} occupations with source_url to {OCC_PATH}.")


if __name__ == "__main__":
    main()
