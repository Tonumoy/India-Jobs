"""
Generate rich Markdown descriptions for each occupation in `pages/<slug>.md`.

These descriptions are what the LLM reads when scoring. The richer they are,
the better the score. For occupations where we have specific industry context
(e.g. TCS engineers — we know about the 12,000-layoff announcement), we
include it. For others, we generate a structured template from the
occupations.json fields.

Usage:
  uv run python pipeline/process.py            # generate all
  uv run python pipeline/process.py --force    # overwrite existing
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path

from make_prompt import EDU_LABELS, HIRE_LABELS

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
PAGES_DIR = ROOT / "pages"


# Hand-curated context for the occupations with the most specific industry data.
# Add to this dict as you research more occupations.
RICH_CONTEXT: dict[str, str] = {
    "tcs-engineers": """\
Tata Consultancy Services (TCS) is India's largest IT services firm by headcount, with 607,979 employees at FY25 close. Most employees are software engineers working on offshore-delivered application development, maintenance, testing, and digital transformation projects for Fortune 500 clients. The bulk of work is mid-tier coding, code review, defect resolution, and platform configuration — work that AI coding assistants now perform with significant productivity uplift.

In July 2025, TCS announced its largest layoff in history: 12,000 employees globally, predominantly mid-level engineers whose deployment is no longer feasible amid the AI transformation. CEO K Krithivasan called it "the toughest decision of my career." A year earlier he had told the Financial Times that AI would make most incoming call-center calls unnecessary.

The pyramid model — hire 600K freshers a year, train in Java, bill to clients — is being directly disintermediated by AI coding tools. Net headcount at the top five Indian IT firms declined by 57,891 across FY24 and FY25 combined, even as their combined revenue grew. This is the canonical Indian AI-exposure story.
""",
    "infosys-engineers": """\
Infosys is India's second-largest IT services firm with 323,578 employees at FY25 close. The role mix and work delivered closely mirror TCS: offshore-delivered application development, ERP implementation, testing, and increasingly, AI/agent platform work via Infosys Topaz.

In FY24, Infosys posted its first-ever annual headcount decline (-25,994). FY25 was roughly flat. CEO Salil Parekh has publicly invoked the Jevons paradox — arguing that 10× AI productivity will create demand for 10× more software, and therefore 10× more engineers. Infosys claims it has trained 270,000 employees (84% of workforce) to be "AI-aware" and built 200+ internal AI agents.

The verdict is unresolved. Indian IT-services pricing is still per-FTE — and clients are now mandating per-outcome contracts. Mid-tier engineers are most exposed; senior architects and AI specialists less so.
""",
    "bpm-voice": """\
India is the world's outsourcing capital for voice-based customer support. Approximately 700,000 agents work in call centres across NCR, Bengaluru, Hyderabad, Pune, Chennai, Mumbai, and tier-2 cities like Indore, Jaipur, and Ahmedabad. They handle inbound and outbound calls for international clients in banking, telecom, retail, healthcare, and travel.

The work is highly scripted: greet customer, identify, authenticate, classify intent, follow decision tree, resolve or escalate. This is exactly what modern voice AI agents do today — and at a fraction of the cost. LimeChat, a Bengaluru AI-agent startup, prices at roughly ₹1,00,000/month, replacing 15 human agents. Haptik (Reliance-owned) sells voice agents at $120/month per deployed lane.

Net BPM hiring in India fell from 177,000 (FY22) to under 17,000 in each of FY24 and FY25 — a tenfold collapse (TeamLease Digital, via Reuters, October 2025). Pramod Bhasin, who founded India's first BPO at GE Capital in 1997 and later founded Genpact, told Reuters in October 2025: "The biggest impact is going to be on young students coming out of college."
""",
    "bpm-data-entry": """\
Data entry and processing roles in Indian BPM cover transcription of forms, invoices, claims, and surveys into structured databases. Typical tasks: read scanned documents, key fields into ERP or claims systems, flag exceptions for human review. Almost all work is screen-and-keyboard.

This task category is one of the highest-confidence AI substitution cases. Modern document-understanding models (Azure Document Intelligence, AWS Textract, Anthropic Claude with vision, Google Gemini) parse the same forms at far higher accuracy than human entry clerks, with audit trails. The remaining 5-10% exception cases are increasingly handled by AI agents with human-in-the-loop review.

Indian BPM firms have been quietly reducing data-entry headcount for years; the BPM segment's net hiring collapse is concentrated here. Median pay is among the lowest in the formal economy (~₹2.2L/year), making the workers structurally vulnerable.
""",
    "content-writers": """\
Content writers in India work across SEO blog content, marketing collateral, product descriptions, social media copy, and ghost-written newsletters. Most agency work is delivered at $0.02-$0.10/word, with Indian writers competing globally on Upwork, Contently, and direct client engagements.

This is among the most directly substituted occupations by current AI. ChatGPT-4-class models produce content at quality indistinguishable from median agency writers, at a fraction of the cost. The pricing floor is collapsing — agencies that paid $40/article in 2022 now pay $10 in 2026, with the implicit assumption that the writer is "editing AI output," not generating from scratch.

A subset of writers have moved into AI-prompt engineering and content strategy roles, but the base population of working content writers has contracted sharply since 2023. Industry estimates put the active Indian content-writer population at 450,000, down materially from peak.
""",
    "gcc-aiml": """\
GCC AI/ML specialists are in-house AI engineers, ML researchers, and data scientists at Indian-based Global Capability Centres of multinational firms (Google, Microsoft, JPMorgan, Goldman Sachs, Walmart, Target, Wells Fargo, Cisco, etc.). Per Zinnov-NASSCOM 2025, India hosts 120,000+ such professionals across 185+ AI/ML Centres of Excellence.

Work is largely product engineering: training models, building MLOps platforms, productionizing GenAI use-cases, building proprietary agents for the parent company. Compensation is sharply higher than IT services (₹30-50L/year typical, vs ₹6-8L at TCS) and the work is closer to the global frontier.

This is one of the few Indian occupational categories where AI is a tailwind, not a headwind. The same forces shrinking the IT services pyramid are growing this segment — though the absolute numbers are far smaller than the displacement. AI specialists are the occupational layer that *benefits* from the broader exposure.
""",
    "cultivators": """\
Self-employed farmers cultivating land they own or rent. India has approximately 119 million cultivators per PLFS 2023-24, making this one of the largest single occupational categories in the world.

The work is physical, weather-dependent, and tied to specific land. AI applications exist (satellite-based crop monitoring, pest detection apps like Plantix, soil-testing services) but they augment decisions rather than substitute the labour. Median income is among the lowest in the economy (~₹1.1L/year, often below the poverty threshold). The bottleneck on automation is capital cost, not AI capability — Indian holdings are small (avg 1.1 hectares) and mechanisation is uneconomic at that scale.
""",
    "translators": """\
Professional translators in India work between Indian and foreign languages (Hindi-English, regional-English, Indian language pairs) for legal documents, subtitles, technical manuals, government filings, and academic publications. The Indian translation industry historically benefited from a deep multilingual talent pool and low rates.

Neural machine translation (Google Translate, DeepL, and now multimodal LLMs) reached near-human quality for most language pairs by 2023. The remaining demand is for specialised domains (legal, medical, literary) and post-editing of machine output. Volume-based translation work has collapsed; per-word rates have fallen 60-80% since 2022.

A small subset of translators have pivoted to specialised consulting and AI-translation QA. The bulk of the 180,000 estimated practitioners face direct substitution.
""",
}


def render_default(occ: dict) -> str:
    """Generate a structured Markdown template for an occupation without rich context."""
    edu = EDU_LABELS[occ["edu"]]
    hire = HIRE_LABELS[occ["hire"]]
    pay_lakh = occ["pay"] / 100000
    md = f"""# {occ['name']}

**Sector:** {occ['sector']}
**Estimated employment in India:** {occ['value']:,} workers
**Median pay:** ₹{pay_lakh:.1f} lakh per year
**Typical education:** {edu}
**Recent hiring trend:** {hire}
**Primary data source:** {occ['source']}

## About this role

This occupation falls within India's {occ['sector']} sector. Workers in this role typically have {edu.lower()} qualifications and earn around ₹{pay_lakh:.1f} lakh per year on average, with substantial variation by region, employer, and experience.

The hiring trajectory in recent years has been: **{hire.lower()}**. This signal is derived from {occ['source']}.

## Tasks and work environment

(Detailed task description would be sourced from the National Classification of Occupations 2015 (NCO) entry for this role. The seed dataset includes structured fields only; the rich descriptions in this file are generated for occupations where industry-specific context is available — see `pipeline/process.py` for the RICH_CONTEXT dictionary.)
"""
    return md


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite existing pages")
    args = parser.parse_args()

    with open(DATA_DIR / "occupations.json") as f:
        bundle = json.load(f)

    PAGES_DIR.mkdir(exist_ok=True)

    written = 0
    skipped = 0
    for occ in bundle["occupations"]:
        slug = occ["slug"]
        path = PAGES_DIR / f"{slug}.md"
        if path.exists() and not args.force:
            skipped += 1
            continue

        # Header for rich-context entries
        if slug in RICH_CONTEXT:
            rich = RICH_CONTEXT[slug]
            edu = EDU_LABELS[occ["edu"]]
            hire = HIRE_LABELS[occ["hire"]]
            md = f"""# {occ['name']}

**Sector:** {occ['sector']}
**Estimated employment in India:** {occ['value']:,} workers
**Median pay:** ₹{occ['pay'] / 100000:.1f} lakh per year
**Typical education:** {edu}
**Recent hiring trend:** {hire}
**Primary data source:** {occ['source']}

## About this role

{rich}
"""
        else:
            md = render_default(occ)

        path.write_text(md, encoding="utf-8")
        written += 1

    print(f"Wrote {written} markdown pages, skipped {skipped} existing. Total: {len(bundle['occupations'])}")


if __name__ == "__main__":
    main()
