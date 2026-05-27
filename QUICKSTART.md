# Quickstart

This is the "I just want to get it running" guide. The full README has the deep dive.

## What this repo actually does, in plain English

```
   You / Your data
        │
        ▼
   data/occupations.json    ← Master list: 90 Indian occupations, sized by employment,
        │                      with median pay, education, hiring trend, sources.
        │                      Currently hand-curated from PLFS, NASSCOM, NSDC, company filings.
        │
        ├──► pipeline/process.py  ──►  pages/*.md
        │     "Turn each occupation into a rich       (One markdown file per occupation.
        │      description an LLM can read."          These are what the LLM sees.)
        │
        ├──► pipeline/score.py    ──►  data/scores.json
        │     "Send each pages/*.md to an LLM,        (The LLM's AI-exposure score 0-10
        │      ask it to score AI exposure 0-10."     + a rationale, per occupation.)
        │
        ├──► pipeline/make_csv.py ──►  data/occupations.csv
        │     "Flatten everything into a CSV."         (For Excel/spreadsheet exploration.)
        │
        └──► pipeline/build_site_data.py ──► site/data.json
              "Merge occupations + scores."            (39KB. The frontend fetches this.)

   site/index.html  ←  loads site/data.json at runtime, renders the treemap.
```

## What LLM is being used right now?

**Currently: NONE at runtime.** Here's the truth:

- The `data/scores.json` that ships with this repo contains scores **I wrote by hand**, calibrated to the rubric in `pipeline/make_prompt.py`. They're reasonable starting points but they're not LLM output.
- If you do nothing else and just deploy the site, it will display my hand-written scores. That's fine for a first deploy.
- **When you run `make score`** (or `uv run python pipeline/score.py`), the script sends each occupation to **Google Gemini 2.5 Flash via OpenRouter** (this is the default in `pipeline/score.py`, the same model family Karpathy uses for the US version). It will overwrite `data/scores.json` with real LLM output, and you can use any model on OpenRouter (Claude, GPT, Llama, Gemini, etc.) by passing `--model anthropic/claude-3.5-sonnet` or similar.

So there are two states this project can be in:

| State | What's in scores.json | What it looks like |
|---|---|---|
| **As shipped** | Tonumoy's expert estimates following the rubric | Works, deployable, defensible scores |
| **After `make score`** | Real LLM output (Gemini Flash by default) | More "official" — actual machine judgments |

Most people will deploy as-shipped first, then re-score later when they have an API key.

---

## Three paths based on your goal

### Path A — "I just want to host the thing" (5 minutes, no Python needed)

1. Unzip `india-jobs.zip` on your laptop.
2. Go to [github.com/new](https://github.com/new). Name it `india-jobs`. Make it **Public**. Click **Create repository**.
3. On the empty repo page, click "uploading an existing file". Drag the **contents** of the unzipped folder (not the folder itself — the files inside it) into the upload box. Wait for upload. Click **Commit changes**.
4. In the repo, click **Settings** (top right tabs) → **Pages** (left sidebar).
5. Under "Source", choose **Deploy from a branch**. Under "Branch", pick **main** and folder **`/site`**. Click **Save**.
6. Wait ~30 seconds, then visit `https://<your-github-username>.github.io/india-jobs/`.

That's it. The site is live and shows the hand-curated scores. You haven't used an LLM yet, but the visualization is real and shareable.

### Path B — "I want real LLM scores, not Tonumoy's hand-written ones" (10 minutes)

You'll need Python 3.11+ and `uv` (a Python package manager).

1. **Install uv** — one command:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh    # macOS / Linux
   # or on Windows PowerShell:
   # powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Get a free OpenRouter API key:** [openrouter.ai/keys](https://openrouter.ai/keys). Sign up, click "Create Key", copy it.

3. **Clone (or unzip) the repo locally:**
   ```bash
   git clone https://github.com/<your-username>/india-jobs
   cd india-jobs
   ```

4. **Drop the key into a `.env` file:**
   ```bash
   echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
   ```

5. **Install dependencies and run the pipeline:**
   ```bash
   make install     # installs httpx, dotenv, tqdm, etc.
   make all         # runs pages → score → csv → site (~5 min, costs about $0.05 in API calls)
   ```

   What's happening: it generates the markdown descriptions, sends each one to Gemini Flash, gets a 0-10 score and rationale, builds the CSV, builds the site data.

6. **Preview locally:**
   ```bash
   make serve
   # Open http://localhost:8000
   ```

7. **Commit and push** to update the live site:
   ```bash
   git add -A && git commit -m "Re-scored with Gemini Flash" && git push
   ```
   GitHub Pages auto-rebuilds in ~30 seconds.

### Path C — "I want to score against a different question entirely"

This is the killer feature of Karpathy's architecture. The rubric in `pipeline/make_prompt.py` is one long string. Edit it to ask any question:

- "Score each Indian occupation for **humanoid robotics exposure** over the next 10 years."
- "Score each occupation for **risk of getting offshored to Vietnam/Philippines**."
- "Score each occupation for **climate-displacement risk** (heat exposure, monsoon disruption, etc.)."

Then:
```bash
make rescore       # forces a complete re-run, ignores cache
make site          # rebuild data.json
make serve
```

Your treemap now colors by your new question. Same data, completely different story.

---

## What can go wrong

**"Module not found" errors when running scripts directly:** Use `uv run python pipeline/...` (or the Makefile) rather than `python pipeline/...`. The scripts import `make_prompt` from the same directory, which works under `uv run` but can break under bare python depending on your shell.

**Site loads but the treemap is blank:** Open browser DevTools (F12) → Console. If you see "Failed to load resource: data.json" — the file isn't where the page expects it. Run `make site` to regenerate, then make sure both `index.html` and `data.json` are in the same `site/` folder.

**OpenRouter returns 401:** The `.env` file isn't being read. Check that `.env` is in the repo root (not in `pipeline/`), and that the line is exactly `OPENROUTER_API_KEY=sk-or-v1-...` (no quotes, no spaces).

**GitHub Pages shows 404:** The Pages source path is wrong. In Settings → Pages, make sure the folder is `/site`, not `/` (root) or `/docs`.

**The hover tooltip doesn't show on mobile:** That's expected — there's no hover on touch devices. I should probably add a tap handler. Open an issue and I'll fix it (or fork and fix).

---

## What I think you should actually do

Honestly? **Path A first.** Get it live in 5 minutes with the hand-curated scores. Post it. See if the LinkedIn post lands. If it does and you want to harden the credibility, run Path B and replace the scores with real LLM output, then push an update.

The hand-curated scores aren't a weakness — they're a deliberate starting point so the project deploys out of the box. Karpathy's `scores.json` is committed too; he doesn't expect every fork to re-run the LLM step.
