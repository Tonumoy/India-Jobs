# India Jobs — one-command pipeline
# Usage: just type `make` to see what each command does.

.PHONY: help install pages score csv site serve rescore clean all

help:
	@echo "India Jobs pipeline — common commands:"
	@echo ""
	@echo "  make install     Install Python dependencies (uses uv)"
	@echo "  make pages       Generate pages/*.md from occupations.json"
	@echo "  make score       Run LLM scoring (needs OPENROUTER_API_KEY in .env)"
	@echo "  make csv         Build data/occupations.csv"
	@echo "  make site        Build data.json from sources + scores"
	@echo "  make serve       Serve the site locally at http://localhost:8000"
	@echo ""
	@echo "  make all         Run the full pipeline (pages → score → csv → site)"
	@echo "  make rescore     Force re-score all occupations with the LLM"
	@echo "  make clean       Remove generated files (keeps source data)"
	@echo ""
	@echo "First time? See QUICKSTART.md"

install:
	uv sync

pages:
	uv run python pipeline/process.py

score:
	uv run python pipeline/score.py

rescore:
	uv run python pipeline/score.py --force

csv:
	uv run python pipeline/make_csv.py

site:
	uv run python pipeline/build_site_data.py

all: pages score csv site
	@echo ""
	@echo "✓ Pipeline complete. Now run 'make serve' to view locally."

serve:
	@echo "Serving on http://localhost:8000 — Ctrl+C to stop"
	python -m http.server 8000

clean:
	rm -rf pages/*.md
	rm -f data/occupations.csv
	rm -f data.json
	@echo "Cleaned generated files. Source data in data/occupations.json and data/scores.json preserved."
