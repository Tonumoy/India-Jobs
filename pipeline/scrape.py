"""
Scrape Indian occupational data from official sources.

India has no single equivalent of the US BLS Occupational Outlook Handbook.
This script orchestrates scraping from three complementary sources:

  1. NCO 2015 (National Classification of Occupations)
     - 3,600 occupations, 426 occupational families
     - Source: Directorate General of Employment, Ministry of Labour
     - URL: https://www.dgemployment.gov.in/  (PDF)
     - We use this for canonical occupation titles and task descriptions.

  2. NSDC Sector Skill Council reports
     - 36 SSCs covering all major industries
     - Per-SSC: employment, growth projections, skill gaps, NSQF mappings
     - Source: https://www.nsdcindia.org/
     - We use this for sector-level employment and growth data.

  3. NCS (National Career Service) portal
     - Live job postings and occupation profiles
     - Source: https://www.ncs.gov.in/
     - We use this for current pay-band and demand signals.

Output: raw HTML/PDF cached in `html/` so re-runs are cheap and we never DDoS
the source. The cache is gitignored (large, regenerable).

USAGE:
  uv run python pipeline/scrape.py --source nsdc
  uv run python pipeline/scrape.py --source nco --pdf data/NCO-2015-Vol2.pdf
  uv run python pipeline/scrape.py --source ncs --query "data analyst"

NOTE: This is a SKELETON. The seed dataset in `data/occupations.json` was
hand-curated from these sources. To expand the dataset, implement the
TODO blocks below. The seed data is sufficient to demonstrate the methodology
and run the full scoring + visualization pipeline.
"""

from __future__ import annotations
import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
HTML_DIR = ROOT / "html"


async def scrape_nsdc(skill_council: str | None = None):
    """
    Scrape NSDC Sector Skill Council reports.

    The NSDC site is JavaScript-heavy and requires a headless browser.
    Each SSC has a landing page with downloadable reports (PDFs) and an
    occupations list with NCO mappings.

    TODO: Implement with Playwright. The pattern:
      1. async with async_playwright() as p:
      2.    browser = await p.chromium.launch(headless=True)
      3.    page = await browser.new_page()
      4.    await page.goto("https://www.nsdcindia.org/sector-skill-councils")
      5.    Collect SSC links
      6.    For each SSC: scrape its occupations table + download report PDF
    """
    print("NSDC scraping: not implemented in seed release.")
    print("The seed dataset already covers 244 occupations across 26 sectors.")
    print("To extend: implement the Playwright workflow described in the docstring.")


def scrape_nco_pdf(pdf_path: Path):
    """
    Parse the NCO 2015 PDF (Volumes 1, 2A, 2B) for canonical occupation titles
    and descriptions.

    The NCO PDF structure:
      - Volume 1: Conceptual framework, code structure
      - Volume 2A: Codes 1-5 (managerial, professional, technical)
      - Volume 2B: Codes 6-9 (skilled trades, machine operators, elementary)

    Each occupation entry contains:
      - 8-digit NCO code (e.g., 2511.0100 = Software Developer)
      - Title
      - Brief description
      - Typical tasks
      - Educational requirement
      - Related occupations

    TODO: Implement with pypdf. The pattern:
      1. Open PDF with pypdf.PdfReader
      2. For each page, extract text
      3. Regex for the 8-digit code pattern at the start of each occupation block
      4. Capture the description block until the next code
      5. Write to `pages/<slug>.md` where slug is derived from the title
    """
    if not pdf_path.exists():
        print(f"NCO PDF not found at {pdf_path}.")
        print("Download from: https://www.dgemployment.gov.in/ (search 'NCO 2015')")
        return
    print(f"Would parse {pdf_path}, but this is a skeleton.")
    print("The seed dataset already includes hand-curated descriptions in pages/.")


def scrape_ncs_portal(query: str):
    """
    Scrape the National Career Service (NCS) portal for live demand signals.

    NCS has an Occupation Profiles section with brief descriptions, but the
    most useful data is the live job-posting volume per occupation, which
    serves as a hiring-demand proxy.

    TODO: Implement with httpx + BeautifulSoup. The NCS public search API is at
      https://www.ncs.gov.in/national-career-service/_api/...
    """
    print(f"NCS scrape for query '{query}': not implemented in seed release.")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["nsdc", "nco", "ncs"], required=True)
    parser.add_argument("--pdf", type=Path, help="Path to NCO 2015 PDF (if --source nco)")
    parser.add_argument("--query", type=str, help="Search query (if --source ncs)")
    args = parser.parse_args()

    HTML_DIR.mkdir(exist_ok=True)

    if args.source == "nsdc":
        await scrape_nsdc()
    elif args.source == "nco":
        scrape_nco_pdf(args.pdf or ROOT / "data" / "NCO-2015-Vol2.pdf")
    elif args.source == "ncs":
        if not args.query:
            print("--query required for NCS source.")
            sys.exit(1)
        scrape_ncs_portal(args.query)


if __name__ == "__main__":
    asyncio.run(main())
