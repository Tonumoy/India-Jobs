# CLAUDE.md — orientation for AI coding agents

This file briefs a Claude (or other LLM) agent walking into this repo cold. Read it once, then act.

## What this repo is

A static GitHub-Pages site that visualises **AI exposure scores for 244 Indian occupations across 26 sectors** as a D3.js treemap. The scores come from real LLM calls (OpenRouter) using a custom India-specific rubric.

**Live site:** https://tonumoy.github.io/India-Jobs/ (case-sensitive URL).
**Owner:** Tonumoy Mukherjee (LinkedIn: bodhi108, email: tonumoymukherjee2@gmail.com).
**Inspired by:** Andrej Karpathy's [github.com/karpathy/jobs](https://github.com/karpathy/jobs) — same pipeline shape, India-localised data and rubric.

## Repo layout

```
.
├── index.html                 # The whole frontend (D3 treemap, single file)
├── data.json                  # What the frontend fetches at runtime (built artifact)
├── .nojekyll                  # Disables GitHub-Pages Jekyll processing
├── jobs.png                   # Hero image for the README
├── data/
│   ├── occupations.json       # ★ Master dataset (244 occupations) — source of truth
│   ├── scores.json            # ★ LLM scores per occupation (built artifact)
│   └── occupations.csv        # Flat CSV view (built artifact)
├── pages/<slug>.md            # ★ LLM input: one rich description per occupation (244 files)
├── pipeline/                  # All Python scripts
│   ├── make_prompt.py         # ★ The scoring rubric (SYSTEM_PROMPT lives here)
│   ├── process.py             # Generates pages/*.md from occupations.json
│   ├── score.py               # ★ Calls OpenRouter, writes scores.json (hardened)
│   ├── make_csv.py            # Flattens to data/occupations.csv
│   ├── build_site_data.py     # Merges occupations + scores → data.json
│   ├── add_source_urls.py     # One-shot: maps source citations → URLs
│   ├── expansion_data.py      # Defines new occupations (extensible — append to NEW_OCCUPATIONS)
│   ├── merge_expansion.py     # Merges expansion_data into occupations.json
│   ├── adjust_overlaps.py     # One-shot: corrects double-counting after expansions
│   └── scrape.py              # Skeleton scrapers for PLFS / NSDC / NCO (unused for now)
├── .github/workflows/
│   └── rescore.yml            # ★ Weekly cron: re-runs the pipeline, commits, deploys
├── Makefile                   # Thin wrappers around uv commands
├── pyproject.toml             # Python deps (httpx, dotenv, tqdm, etc.)
├── README.md                  # User-facing docs
├── QUICKSTART.md              # 15-min getting-started guide
└── CLAUDE.md                  # ← you are here
```

★ = the files you'll touch most often.

## Data model

`data/occupations.json` schema:

```json
{
  "meta": {
    "source": "Curated from PLFS 2023-24, NASSCOM, NSDC SSCs, ...",
    "total_occupations": 244,
    "total_sectors": 22,
    "total_workforce_covered": 565585000,
    "last_updated": "2026-05-28",
    "edu_codes":  {"1": "None / Primary", ..., "6": "PhD"},
    "hire_codes": {"-3": "Strongly declining", ..., "3": "Booming"}
  },
  "occupations": [
    {
      "slug": "tcs-engineers",
      "name": "TCS engineers",
      "sector": "IT Services & Software",
      "value": 607000,                    // employment headcount in India
      "pay":   600000,                    // ₹/year, median
      "edu":   4,                         // 1-6, see edu_codes
      "hire":  -2,                        // -3 to 3, see hire_codes
      "source": "TCS Q4 FY25 + Jul 2025 layoff announcement",
      "source_url": "https://www.tcs.com/investor-relations"
    },
    ...
  ]
}
```

`data/scores.json` schema:

```json
{
  "_meta": {"note": "...", "model": "...", "rubric": "..."},
  "tcs-engineers": {
    "score": 8,
    "rationale": "TCS engineers mainly do offshore coding, testing, ...",
    "model": "nvidia/nemotron-3-super-120b-a12b:free"
  },
  ...
}
```

`data.json` (the built site artifact) groups occupations by sector and uses short keys to keep payload small:
- `n` name, `s` slug, `v` value, `ai` AI score, `h` hire, `p` pay, `e` edu,
- `src` source citation, `u` source URL, `r` LLM rationale.

## How to run the pipeline

**Always use `uv run python ...` (or the Makefile), not bare `python`.** The scripts in `pipeline/` import their siblings (e.g. `from make_prompt import ...`), which works under `uv run` but not always under a system Python.

On Windows where `uv run` sometimes hits Cygwin fork errors, you can also call the venv Python directly:
```bash
./.venv/Scripts/python.exe pipeline/<script>.py
```

```bash
make help            # list all commands

make install         # uv sync — install deps
make pages           # process.py: generate pages/<slug>.md (skips existing unless --force)
make score           # score.py:   score missing occupations
make rescore         # score.py --force: re-score everything
make csv             # make_csv.py
make site            # build_site_data.py: produce data.json
make all             # pages → score → csv → site
make serve           # python -m http.server 8000 (serves the repo root)
make clean           # rm pages/*.md, data/occupations.csv, data.json
```

## How `score.py` is hardened (read before changing it)

Real-world failure modes we've seen and the layered defences in `score.py`:

| Failure mode | Defence |
|---|---|
| `max_tokens` truncates JSON mid-string | `max_tokens=1200` (was 400) + `_repair_truncated_json()` closes the string and braces |
| Model wraps response in ` ```json ... ``` ` | `_strip_fences()` strips them |
| Model returns malformed JSON | `_regex_extract()` pulls `score` + `rationale` directly from the raw text |
| Model returns `content: null` (safety filter) | We check for null/empty and raise a retryable `ValueError` |
| 429 from one model | 5 retries per model with exponential 5–25s backoff |
| All retries on primary fail | 15-model fallback chain in `FALLBACK_MODELS` (largest → smallest free models) |
| One bad occupation kills the run | Per-occupation try/except in `main()` — failures are logged, others continue |
| Windows `cp1252` codec can't encode `‑` etc. | All file reads/writes use `encoding="utf-8"` explicitly |

If you add a new failure mode, follow the same layered-defence pattern. **Don't remove defences** unless you've verified the underlying cause is gone.

## How to add new occupations

```python
# pipeline/expansion_data.py — append to NEW_OCCUPATIONS:
{"slug": "my-new-role", "name": "My new role",
 "sector": "IT Services & Software",       # must exist already, OR be in NEW_SECTORS
 "value": 50000, "pay": 600000, "edu": 4, "hire": 2,
 "source": "Some Indian source", "source_url": "https://example.com/"},
```

Then:
```bash
uv run python pipeline/merge_expansion.py     # appends (skips existing slugs)
uv run python pipeline/process.py             # generates pages/my-new-role.md
uv run python pipeline/score.py               # scores only the new ones
uv run python pipeline/build_site_data.py     # rebuilds data.json
git add -A && git commit -m "Add N new occupations" && git push
```

If a new occupation overlaps an existing aggregate category (e.g. you add "plumbers" while "construction-labour" already lumps them in), record the adjustment in `pipeline/adjust_overlaps.py` so future rebuilds don't double-count.

## How to change the rubric

Edit `SYSTEM_PROMPT` in [pipeline/make_prompt.py](pipeline/make_prompt.py). The rubric defines what the LLM is scoring (AI exposure, robotics, offshoring risk, etc.). The output format is fixed:

```json
{"score": <int 0-10>, "rationale": "<2-3 sentences, ≤75 words>"}
```

After editing, `make rescore && make site` to rebuild against the new rubric.

## Frontend (index.html)

Single static file. Loads `data.json`, renders a D3 treemap. Important regions:

- **CSS** (`<style>`): colour vars, tile / tooltip / footer styling.
- **Sector labels:** sectors get a translucent strip with the sector name across the top of their block.
- **Tile rendering** (`render()` near line ~597): builds each leaf, applies colour from the active layer, attaches mousemove (tooltip) and click (open `d.u` in new tab) listeners.
- **Layers** (`LAYERS` object): four named colour scales — `ai`, `hire`, `pay`, `edu`. Each has `color(d)`, `metric(d)`, `legendMin/Max`, `stops`. Add a new layer by adding a key here and a button row in the HTML.
- **Stats panel** (`updateStats()`): the cards under the buttons; per-layer summary numbers.
- **Tooltip** (`showTooltip()`): renders the per-tile HTML.

The frontend is intentionally framework-free — no build step, edit in place, refresh.

## GitHub Actions

`.github/workflows/rescore.yml` runs the full pipeline every Monday 04:00 IST (UTC 22:30 Sunday). It needs the repository secret `OPENROUTER_API_KEY`. The job:

1. Checks out main.
2. Installs uv via `astral-sh/setup-uv@v3`.
3. `uv sync`.
4. Runs `pipeline/score.py --force` against the primary free model.
5. Runs `build_site_data.py` and `make_csv.py`.
6. Commits the artifacts as `github-actions[bot]` if anything changed, and pushes.

GitHub Pages then re-deploys automatically.

You can trigger the workflow manually via **Actions → Weekly rescore → Run workflow**.

## Deployment

GitHub Pages is configured: **main branch, `/(root)`**. `.nojekyll` exists so Pages serves the static files verbatim (otherwise it would try to render `README.md` as the index). **Don't move `index.html` or `data.json`** — they must stay at the repo root.

URL: https://tonumoy.github.io/India-Jobs/ (case-sensitive!).

## Conventions and gotchas

- **No emojis** in code, commits, or generated files unless explicitly asked.
- **Windows shell:** PowerShell is the default. Use Bash via Git Bash when convenient (the agent harness exposes both). Beware that `uv` sometimes hits `cygheap read copy failed` errors in heavy parallel use; falling back to `./.venv/Scripts/python.exe` works.
- **UTF-8 everywhere.** Always `encoding="utf-8"` for file IO — Windows defaults to cp1252 and Indian sources commonly contain `‑`, `₹`, `–`, smart quotes.
- **Case-sensitive Pages URL.** `India-Jobs`, never `india-jobs`.
- **`.env` is gitignored.** The `OPENROUTER_API_KEY` value lives in `.env` locally and as a GitHub Actions secret remotely. If a user pastes a key in chat, advise them to rotate it.
- **`source_url` on every occupation** — don't add a new row without one. The frontend uses it for clickable tiles.
- **Total workforce can legitimately exceed PLFS's ~480M** — we include informal categories (domestic workers, religious workers, street vendors, gig delivery) that PLFS under-samples.
- **Don't introduce backwards-compat shims.** When the dataset, schema, or pipeline changes, fix the call sites; don't leave both versions running.

## Delegating future work to AI agents

This repo is designed to be operated by AI coding agents (like a Claude Code session). Here's how to do that well.

### Tasks that automate cleanly

- **Re-scoring** with a different model or rubric.
- **Adding new occupations** (append to `expansion_data.py`, run the merge/process/score/build chain).
- **UI tweaks** in `index.html` (colour, layout, tooltip, layers).
- **New layers** — extending `LAYERS` to add an additional colour-coded view.
- **README/QUICKSTART updates** when state changes.

### Tasks that need a human in the loop

- **Sourcing employment numbers** for a new occupation — the agent can pick a plausible source from NSDC/NASSCOM/ministry/regulator lists but you should sanity-check the number against the cited PDF.
- **API key rotation** — secrets go through the GitHub UI, not the CLI.
- **GitHub Pages settings** — branch / folder choice can't be set by the agent.

### Recommended workflow per task

1. **Open a Claude Code session** with this repo as the working directory.
2. **State the goal in 1–3 sentences**: what you want changed, which file(s) it lives in, what "done" looks like. Cite paths, e.g. `index.html:597` for tile rendering. The agent should not need to grep the repo to find common targets — they're listed above.
3. **Let the agent plan, edit, and commit.** Review the diff before push.
4. **For multi-hour work** (e.g. full re-score on free models): run it in the background (`run_in_background: true` in the agent's harness) and let the agent notify you on completion.
5. **For ambient maintenance** (e.g. "keep adding new occupations as Indian gig categories evolve"): use a scheduled / cron agent that runs `pipeline/merge_expansion.py` weekly off an expanding `expansion_data.py`.

### Prompt patterns that work well

- "Add a new layer to `index.html` that colours by **gender-gap risk**. Define a new rubric in a new `make_prompt_gender.py`, run scoring with it, store the new scores under a key in `data/scores.json`, and add a button + colour scale. Don't break existing layers."
- "Fork the rubric in `make_prompt.py` to score for **climate-displacement risk** instead of AI exposure. Save the new rubric in a sibling file, add a CLI flag to `score.py` to choose rubric, re-score against it, commit with a clear message."
- "There's a typo in the rationale for `<slug>`. Find it, re-score just that occupation with `--only <slug>` against the current rubric, push."
- "Run a full re-score against `openai/gpt-oss-120b:free` and compare the score distribution to the current Nemotron run. Output a Markdown summary."

### Prompt anti-patterns

- "Improve the project." (Too vague — the agent will guess at priorities.)
- "Add lots of new occupations." (Number? Sectors? Sources? Specify.)
- "Make it better on mobile." (Pick a concrete acceptance test: "tile click on iPhone Safari opens the source link", "tooltip pins on first tap and dismisses on second tap".)

### What the agent should remember between sessions

The user's preferences (saved to `~/.claude/projects/d--India-Jobs/memory/` automatically by the harness):

- The user wants **zero failures** in scoring — design defensively, use the existing fallback chain.
- The user **does not want to spend money** on LLM calls — always default to `:free` OpenRouter models.
- The user prefers **simple, easy-to-understand** documentation — no jargon, no over-engineered explanations.
- The user is happy to delegate aggressively — phrase plans, then execute. Confirm only on irreversible or scope-expanding decisions.

## Quick reference card

```
LIVE URL          https://tonumoy.github.io/India-Jobs/
REPO              https://github.com/Tonumoy/India-Jobs
DEFAULT MODEL     nvidia/nemotron-3-super-120b-a12b:free
FALLBACK MODELS   see FALLBACK_MODELS in pipeline/score.py
RESCORE CRON      Mon 04:00 IST (Sun 22:30 UTC)
SECRET NEEDED     OPENROUTER_API_KEY  (GitHub Actions)
LOCAL ENV         .env  (gitignored)  with OPENROUTER_API_KEY=sk-or-v1-...
DEPLOYS ON        any push to main, via Pages, ~30s
TOTAL OCCS        244 across 26 sectors, ~566M workers
```

## Frontend UI patterns (added Phase D)

The `index.html` redesign added several patterns worth knowing:

- **Sector icons.** `SECTOR_ICONS` is a map from sector name → emoji. When adding a new sector, **add an entry here too** or its strip will have no icon. Keep the icon emoji-only (no external icon font) so the site stays a single-file static deploy.
- **Detail card (was: tooltip).** One `<div id="card">` serves both desktop hover-floating and mobile bottom-sheet roles. On desktop without a pinned tile, it follows cursor and clamps to viewport. On a touch device or after `click`, it becomes "pinned" → on mobile that means full-width bottom sheet with backdrop and drag-handle visual. Don't fork into separate desktop/mobile components.
- **Touch detection.** `IS_TOUCH = matchMedia('(hover: none)').matches || 'ontouchstart' in window`. Use this rather than `userAgent` sniffing.
- **Card behaviour on click.** First click pins the card (mobile or desktop). Second click on the same tile opens the source URL. The card's "Open source ↗" button is the primary CTA inside the card itself.
- **Search.** Top-level search input dims non-matching tiles and gives matching tiles an `.match` outline + glow. Substring match against occupation name OR sector name, case-insensitive.
- **Onboarding hint.** Pill at bottom-center, shown once per browser (localStorage key `indiajobs-onboarded-v2`). Bump the suffix when copy materially changes so returning visitors see it again.
- **Help modal.** Triggered by header `?` button OR the `Click here` link in the lede. Keyboard `Esc` closes both card and modal.
- **Glassmorphism.** `backdrop-filter: blur(18px) saturate(1.15)` on `.card`. Safari support is via `-webkit-backdrop-filter`. Don't add more layers of blur — the GPU cost on lower-end devices stacks badly.

When adding a new layer or feature, the conventions to preserve:
- Pill-style controls (`.pill` class) — never go back to square buttons.
- Layer toggle button has an emoji-prefixed label.
- Stats use the seven-column grid; add new stats by appending to `updateStats()` per current layer.
- Don't use any framework or bundler — the site is one HTML file, period.
