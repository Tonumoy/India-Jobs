# AI Exposure of the Indian Job Market

An interactive treemap of every major occupation in the Indian economy, scored 0–10 for AI exposure by a large language model using an India-specific rubric.

**Live demo:** [tonumoy.github.io/India-Jobs](https://tonumoy.github.io/India-Jobs/)

**New here? Read [QUICKSTART.md](QUICKSTART.md) first** — it gets you from zero to a live, working site in under 15 minutes.

![India Jobs Treemap](jobs.png)

Inspired by Andrej Karpathy's [US Job Market Visualizer](https://karpathy.ai/jobs/) ([source](https://github.com/karpathy/jobs)). Same pipeline architecture, India-localized data and rubric.

## What this is

India has no single equivalent of the US Bureau of Labor Statistics' Occupational Outlook Handbook. So this repo merges multiple Indian sources into a unified dataset of **214 occupations covering ~554 million workers across 22 sectors**, scores each one's AI exposure using an LLM with an India-specific rubric, and renders the result as an interactive treemap.

- **Area** of each tile = total employment in that occupation.
- **Color** = the selected metric (AI exposure / hiring trend / median pay / education).
- **Hover** any tile for the LLM-written rationale and the underlying numbers.
- **Click** any tile to open the original report (PLFS / NASSCOM / NSDC / ministry / regulator).

## How the scores are produced

The scores in `data/scores.json` are **real LLM output**. Each occupation is sent to an OpenRouter model along with the rubric in `pipeline/make_prompt.py`, which returns a 0–10 score and a 2–3 sentence rationale.

We default to free OpenRouter models (no spend):
- **Primary:** `nvidia/nemotron-3-super-120b-a12b:free`
- **Fallback chain:** `openai/gpt-oss-120b:free`, then 13 others ([pipeline/score.py](pipeline/score.py))

The scoring script is hardened against rate-limits, truncated JSON, null responses, and provider outages. If a model 429s, we retry; if all 5 retries fail, we fall over to the next model in the chain. We've run full re-scores end-to-end with zero failures.

## Data pipeline

```
   Indian data sources (PLFS, NASSCOM, NSDC SSCs, NSO, ministries,
   regulator filings, professional councils, company filings)
                          │
                          │  hand-curated
                          ▼
              data/occupations.json   ← Master list: 214 occupations,
                          │              22 sectors, with source_url per row
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
  pipeline/         pipeline/           pipeline/
  process.py        score.py            make_csv.py
       │                  │                  │
       ▼                  ▼                  ▼
   pages/*.md     data/scores.json    data/occupations.csv
       │                  │
       └────────┬─────────┘
                ▼
       pipeline/build_site_data.py
                │
                ▼
            data.json   ←  the file the frontend fetches
                ▲
                │  fetch()
            index.html   ←  treemap (D3.js, single static file)
```

| Stage | Script | Reads | Writes |
|---|---|---|---|
| Curate | `data/occupations.json` (hand-edited) | source reports | structured rows |
| Describe | `pipeline/process.py` | `data/occupations.json` | `pages/<slug>.md` |
| Score | `pipeline/score.py` | `pages/*.md` + rubric | `data/scores.json` |
| Tabulate | `pipeline/make_csv.py` | both above | `data/occupations.csv` |
| Build | `pipeline/build_site_data.py` | both above | `data.json` |
| Render | `index.html` | `data.json` | treemap in the browser |

## Auto-update

`.github/workflows/rescore.yml` runs **every Monday at 04:00 IST**. It re-runs the full pipeline on GitHub's servers using the `OPENROUTER_API_KEY` repository secret, commits any updated `data.json` / `scores.json` / `occupations.csv` to `main`, and GitHub Pages re-deploys automatically. Each run costs $0 (free models).

You can also trigger it manually at any time: **Actions → Weekly rescore → Run workflow**.

## Setup (local)

```bash
# Clone
git clone https://github.com/Tonumoy/India-Jobs
cd India-Jobs

# Install uv (Python package manager)
#   macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
#   Windows PS:  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install deps
uv sync

# (Optional) Add your OpenRouter API key for re-scoring
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
```

A free OpenRouter key is at [openrouter.ai/keys](https://openrouter.ai/keys). It's only needed if you want to re-score — the repo ships with current scores already in `data/scores.json`.

## Common commands

```bash
make help            # show all commands
make all             # full pipeline: pages → score → csv → site
make score           # re-score only what's missing
make rescore         # force re-score everything
make site            # rebuild data.json from current scores
make serve           # serve locally on http://localhost:8000
```

All `make` targets are thin wrappers around `uv run python pipeline/<script>.py`.

## AI exposure scoring

Each occupation is scored on a single **AI Exposure** axis from 0 to 10. The full rubric is in [pipeline/make_prompt.py](pipeline/make_prompt.py). Calibration anchors:

| Score | Meaning | Indian examples |
|---|---|---|
| 0–1 | Minimal | Cultivators, masons, domestic workers, religious workers |
| 2–3 | Low | Doctors, nurses, police, drivers, salon staff |
| 4–5 | Moderate | Civil engineers, retail sales, branch managers, real estate brokers |
| 6–7 | High | TCS/Infosys engineers, accountants, junior lawyers, financial advisors |
| 8–9 | Very high | Bank clerks, paralegals, content writers, data entry, junior analysts |
| 10 | Maximum | Voice call-centre agents, basic translation, medical transcription |

The weighted average across all 214 occupations sits around 2/10 — much lower than the US (~5.3/10) because India's workforce is disproportionately in low-exposure physical, agricultural, and informal-sector work. Within the **formal/cognitive economy** (~80M jobs), exposure is concentrated exactly in India's export specialty: IT services, BPM, KPO, GCC back-office.

### India-specific factors the rubric weights

- **Wage arbitrage erosion** — Indian fresher developer at ₹5L/yr competing with $500/yr of GitHub Copilot.
- **Service-export composition** — Goldman Sachs (2023) identifies 46% of office-and-admin and 44% of legal tasks as automatable, which maps directly onto India's $224B service-export economy.
- **Regulatory and informal-sector protection** — Government clerks have automatable tasks but protected employment; we score the technology, flag the protection.
- **Infrastructure constraints** — Robotics adoption lags because Indian labour is cheap relative to capital.

## Forking the rubric

The most powerful customisation: write any 0–10 scoring rubric, re-run, get a new colour layer.

```python
# pipeline/make_prompt.py
SYSTEM_PROMPT = """You are evaluating Indian occupations for exposure to
humanoid robotics over the next 10 years. Score 0 = no impact, 10 = full
robotic substitution likely. ..."""
```

```bash
make rescore        # force-re-score everything against the new rubric
make site           # rebuild data.json
```

Same data, completely different story. Works for offshoring risk, climate exposure, gender-displacement risk — any question phrasable as a 0–10 rubric.

## Adding new occupations

The dataset is extensible without manual JSON edits. Add new entries to [pipeline/expansion_data.py](pipeline/expansion_data.py), then:

```bash
uv run python pipeline/merge_expansion.py     # merges into occupations.json (skips dups)
uv run python pipeline/process.py             # generates the new pages/<slug>.md
uv run python pipeline/score.py               # scores only the new ones
uv run python pipeline/build_site_data.py     # rebuilds data.json
git add -A && git commit -m "Add N new occupations" && git push
```

## Deploy

The repo is already configured to deploy to GitHub Pages from `main` / `(root)`. A `.nojekyll` file at the root disables Jekyll so the static files are served verbatim. Any push to `main` triggers a re-deploy in ~30 seconds.

## Caveats

- The scores are **rough LLM estimates**, not rigorous predictions. They depend on the rubric and the model.
- Many high-exposure jobs will be **reshaped**, not replaced.
- Employment counts are reconciled from multiple Indian sources. Where sources disagreed we took the more conservative number. Total coverage sums to ~554M, which exceeds India's ~480M PLFS-formal total — because informal categories (domestic workers, religious workers, street vendors, gig delivery) are systematically under-counted by PLFS but explicitly visible here.

## License

MIT. Fork, modify, write your own prompts, post your own visualizations.

## Built by

[Tonumoy Mukherjee](https://www.linkedin.com/in/bodhi108/)
