# Quickstart

The "I just want to get it running" guide. The full [README.md](README.md) has the deep dive.

## What this repo actually does, in plain English

```
   Indian data sources (PLFS, NASSCOM, NSDC, ministries, regulators, ...)
                          │
                          ▼
   data/occupations.json   ← Master list: 244 Indian occupations, sized by
        │                     employment, with median pay, education, hiring
        │                     trend, source, and source URL.
        │
        ├──► pipeline/process.py  ──►  pages/*.md
        │     "Turn each occupation into a rich       (One markdown file per
        │      description an LLM can read."          occupation. LLM input.)
        │
        ├──► pipeline/score.py    ──►  data/scores.json
        │     "Send each pages/*.md to an LLM,        (The LLM's AI-exposure
        │      ask it to score 0-10 + a rationale."    score 0-10, per occupation.)
        │
        ├──► pipeline/make_csv.py ──►  data/occupations.csv
        │     "Flatten everything into a CSV."        (For Excel exploration.)
        │
        └──► pipeline/build_site_data.py ──► data.json
              "Merge occupations + scores."           (~140KB. Frontend fetches this.)

   index.html  ←  loads data.json at runtime, renders the treemap.
```

## What's in scores.json right now

**Real LLM output.** Every one of the 244 occupations was scored by an OpenRouter model (primary: `nvidia/nemotron-3-super-120b-a12b:free`, fallback: `openai/gpt-oss-120b:free`). Each entry has `score`, `rationale`, and `model`.

The full pipeline re-runs automatically every Monday at 04:00 IST via [.github/workflows/rescore.yml](.github/workflows/rescore.yml), so the live site stays current as model quality improves. All scoring uses **free OpenRouter models — $0 cost per re-score**.

---

## Three paths based on your goal

### Path A — "I just want to host it" (5 minutes, no Python needed)

The repo is already configured for GitHub Pages. If you fork:

1. Fork the repo on GitHub.
2. In the fork: **Settings → Pages** → **Source: Deploy from a branch** → **Branch: main**, **Folder: `/(root)`** → **Save**.
3. Wait ~30 seconds, then visit `https://<your-username>.github.io/<repo-name>/` (case-sensitive — must match the repo name exactly).

Done. The site is live with the current scores.

### Path B — "I want to re-score with my own LLM" (15 minutes, $0)

You'll need Python 3.11+ and `uv` (a Python package manager).

1. **Install uv:**
   ```powershell
   # Windows PowerShell (run as your user — no admin needed):
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   ```bash
   # macOS / Linux:
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Close and reopen your terminal so PATH refreshes. Verify with `uv --version`.

2. **Get a free OpenRouter API key:** sign up at [openrouter.ai/keys](https://openrouter.ai/keys), click **Create Key**, copy it.

3. **Clone and configure:**
   ```bash
   git clone https://github.com/<your-username>/India-Jobs
   cd India-Jobs
   echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
   ```

4. **Install dependencies and run the pipeline:**
   ```bash
   make install   # uv sync
   make rescore   # force re-score with the default free model
   make site      # rebuild data.json
   ```
   Takes ~30 min – 3 hours depending on free-tier rate-limits. Cost: $0.

5. **Preview locally:**
   ```bash
   make serve
   # Open http://localhost:8000
   ```

6. **Push to update the live site:**
   ```bash
   git add -A && git commit -m "Re-score" && git push
   ```
   GitHub Pages re-deploys in ~30 seconds.

### Path C — "I want to score against a different question entirely"

The killer feature of this architecture: write any 0–10 rubric, re-score, get a new colour layer. Edit `pipeline/make_prompt.py`'s `SYSTEM_PROMPT` to ask anything:

- "Score each Indian occupation for **humanoid robotics exposure** over the next 10 years."
- "Score each occupation for **risk of getting offshored to Vietnam/Philippines**."
- "Score each occupation for **climate-displacement risk** (heat, monsoon disruption, etc.)."

Then:
```bash
make rescore    # ignores cache, re-runs everything
make site       # rebuild data.json
make serve      # preview
git add -A && git commit -m "Re-score for humanoid robotics" && git push
```

Same data, completely different story.

---

## Enable the weekly auto-rescore (in your fork)

If you forked, the workflow runs but won't have your API key yet:

1. Go to **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `OPENROUTER_API_KEY`. Secret: paste your key. **Add secret.**
3. Manual test: **Actions → Weekly rescore → Run workflow → main → Run**. Takes ~30 min – 3 hours.

Done. Every Monday at 04:00 IST the site auto-refreshes with the latest LLM scores.

---

## What can go wrong

**`uv: command not found` after install:** Close and reopen your terminal — the installer adds `uv` to PATH but the current session won't see it until restart.

**Site loads but the treemap is blank:** Open DevTools (F12) → Console. If you see "Failed to load resource: data.json" — re-run `make site` and check that `index.html` and `data.json` are at the repo root (not in a subfolder).

**OpenRouter returns 401:** The `.env` file isn't being read. Check that `.env` is in the repo root (not in `pipeline/`), and the line is exactly `OPENROUTER_API_KEY=sk-or-v1-...` (no quotes, no spaces, no trailing blank lines).

**OpenRouter returns 429 during scoring:** That's normal — free-tier models are rate-limited. `score.py` has a 15-model fallback chain and retries with exponential backoff. Just let it run.

**GitHub Pages shows 404:** Two common causes — (1) URL is case-sensitive: `tonumoy.github.io/India-Jobs/` works, `tonumoy.github.io/india-jobs/` does not. (2) In **Settings → Pages**, folder must be `/(root)`, not `/docs`.

**Module not found when running scripts directly:** Use `uv run python pipeline/...` (or the `make` targets) rather than bare `python pipeline/...`. The scripts import siblings from the same directory.
