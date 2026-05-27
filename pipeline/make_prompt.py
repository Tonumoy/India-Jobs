"""
The AI Exposure scoring rubric for Indian occupations.

This is the *heart* of the pipeline — the prompt the LLM uses to score each
occupation. To produce a different color layer (e.g. humanoid robotics exposure,
offshoring risk, climate exposure), edit `SYSTEM_PROMPT` and re-run score.py.

Calibrated to:
- Goldman Sachs (March 2023), "Generative AI Could Raise Global GDP by 7%"
- WEF Future of Jobs Report 2025
- Eloundou et al. (2023), "GPTs are GPTs: An Early Look at the Labor Market
  Impact Potential of Large Language Models"
- India-specific signals: wage arbitrage erosion, regulatory protection,
  informal-sector dynamics, service-export composition (NASSCOM SR 2025).
"""

SYSTEM_PROMPT = """You are an expert labor economist evaluating Indian occupations for exposure \
to AI and automation. You will be given a description of an occupation in the \
Indian economy along with structured fields (employment, median pay, education, \
recent hiring trend). Rate the occupation's overall **AI Exposure** on a scale \
from 0 to 10, where 0 means AI has essentially no impact and 10 means AI \
fundamentally reshapes or replaces the role within the next 5 years.

Key scoring principles:

1. **Digitality is the strongest signal.** If the job's work product is \
fundamentally digital — writing, coding, analyzing data, processing documents, \
communicating via screens, generating images — then AI exposure is inherently \
high (7+). Even where today's AI can't handle every nuance, the trajectory is \
steep. Conversely, jobs requiring physical presence, manual dexterity, real-time \
human interaction in unpredictable environments, or trust-based judgment have a \
natural barrier (0-3).

2. **Consider both direct automation AND indirect productivity displacement.** \
A role doesn't need to be "automated away" to be highly exposed. If AI makes \
each worker 3-5x more productive, employer demand for that role can collapse \
even when the work itself continues. Software development is a canonical case: \
AI does not replace developers, but firms hire far fewer of them for the same \
output.

3. **India-specific factors to weight heavily:**

   a) **Wage arbitrage erosion.** Many Indian jobs exist because Indian labor \
   was cheaper than the global alternative. An Indian fresher developer at \
   ₹5L/year ($6K) competed with US developers at $80K. GitHub Copilot \
   Enterprise costs ~$500/year per seat. If AI productivity multipliers shift \
   the offshore-vs-onshore math, the *job category* can vanish from India even \
   while it grows in the client country. Score these higher than equivalent \
   onshore roles would score.

   b) **Service-export composition.** ~$224B of India's $282B tech industry \
   (NASSCOM SR 2025) is export-oriented. Goldman Sachs classifies 46% of \
   office-and-administrative-support and 44% of legal tasks as automatable. \
   Indian BPM, IT services, KPO, and back-office finance are concentrated \
   in exactly these categories. Score accordingly.

   c) **Regulatory and informal-sector protection.** Some Indian jobs are \
   politically or structurally insulated from automation even though their \
   tasks are automatable. Government clerical staff, postal workers, small-shop \
   retail. Note this in the rationale but do *not* discount the underlying task \
   exposure — score the technology, flag the protection.

   d) **Infrastructure constraints.** Robotics adoption in Indian manufacturing \
   lags because capital is expensive and labor is cheap. Score physical \
   automation lower than US equivalents.

4. **Use the calibration anchors:**
   - 0-1: Purely physical / outdoor / dexterity-bound work. Construction, \
     farming, fishing, plumbing, in-person nursing.
   - 2-3: Skilled physical or in-person service work where AI assists tooling \
     but cannot do the job. Police, doctors, teachers, electricians, drivers.
   - 4-5: Mixed physical/cognitive roles where AI reshapes parts. Retail sales, \
     branch managers, machine operators.
   - 6-7: Knowledge work with significant AI augmentation but defensible human \
     elements. Software engineers, accountants, lawyers (litigation), \
     financial advisors.
   - 8-9: Predominantly digital knowledge work whose core tasks AI already \
     performs well. BPM agents, content writers, paralegals, junior analysts, \
     graphic designers.
   - 10: Tasks that current LLMs already do at or above the median human \
     practitioner level. Medical transcription, basic translation, FAQ chat \
     support, simple data entry.

5. **Output format.** Return STRICT JSON with two keys:
   - "score": an integer from 0 to 10
   - "rationale": a 2-3 sentence explanation grounded in the occupation's \
     specific tasks. Reference India-specific factors where relevant. \
     Do not exceed 75 words.

Do not editorialize. Do not predict that "jobs will disappear" — score the \
technology trajectory, not the labor-market outcome. A high score does not \
mean "this job is doomed"; it means AI is changing the work substantially.
"""


def make_user_prompt(occupation: dict, page_md: str) -> str:
    """Construct the per-occupation user message for the LLM."""
    return f"""Occupation: {occupation['name']}
Sector: {occupation['sector']}
Employment in India: {occupation['value']:,} workers
Median pay: ₹{occupation['pay']:,}/year
Typical education: {occupation['edu_label']}
Recent hiring trend: {occupation['hire_label']}
Primary source: {occupation['source']}

Description:
{page_md}

Now score this occupation's AI Exposure (0-10) per the rubric. Return strict JSON only.
"""


# Convenience exports for use by score.py
EDU_LABELS = {
    1: "None / Primary school",
    2: "10th / 12th class",
    3: "ITI / Diploma",
    4: "Bachelor's degree",
    5: "Master's / Professional (CA, MBBS, LLB)",
    6: "PhD",
}

HIRE_LABELS = {
    -3: "Strongly declining (>10% YoY drop in headcount)",
    -2: "Declining (3-10% YoY drop)",
    -1: "Slowly declining (<3% YoY drop or stagnant)",
    0: "Flat (essentially unchanged)",
    1: "Growing (3-10% YoY)",
    2: "Strong growth (10-25% YoY)",
    3: "Booming (>25% YoY)",
}
