# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InfluenceMap visualizes citation-based academic influence as "influence flowers" — radial diagrams with a central ego entity surrounded by the most influential related entities (authors, affiliations, journals, topics). Data comes from the OpenAlex dataset (2025-05-30 snapshot).

## Architecture

Three-tier system with two Flask services:

1. **Konigsberg** (`konigsberg/`): Scoring engine that computes influence from binary graph data using Numba-accelerated algorithms. Runs on port 8081 locally, port 8000 inside Docker.
2. **Webapp** (`webapp/`): User-facing Flask app serving search UI and flower visualizations. Communicates with Konigsberg via HTTP. Runs on port 8000 locally.
3. **Core** (`core/`): Shared modules for OpenAlex API integration and entity type definitions.

### Key files

- `konigsberg/flowers.py` — Core influence computation engine (Numba JIT-compiled)
- `konigsberg/builder.py` — Builds binary graph structure from CSV data
- `konigsberg/preprocessor.py` — Converts OpenAlex JSON snapshots to MAG-compatible CSV
- `konigsberg/app.py` — Flask API (`/get-flower`, `/get-stats`, `/get-node-info`)
- `webapp/views.py` — Main routes and query orchestration
- `webapp/front_end_helper.py` — Response formatting, node deduplication, log scaling
- `webapp/konigsberg_client.py` — HTTP client to Konigsberg service
- `core/search/openalex.py` — Entity name resolution via OpenAlex API
- `core/utils/entity_type.py` — Entity type enum: AUTH, AFFI, JOUR, FSTD

## Development Commands

```bash
# Install (editable mode)
pip install -e .

# Run webapp locally
python -m webapp.app

# Docker deployment (production with 32 Gunicorn workers)
docker compose up --build
```

## Data Pipeline

OpenAlex snapshot (S3) → `preprocessor.py` (JSON→CSV) → `builder.py` (CSV→binary graph) → `konigsberg/bingraph-openalex/` (~88GB)

See `HowTo.md` for detailed data processing steps.

## Technical Notes

- Numba is used extensively in `flowers.py` for JIT-compiled graph traversal — be careful with type annotations and array operations (recent commits fix `NumbaTypeSafetyWarning` and signed int casting issues)
- Entity types map to OpenAlex concepts: AUTH=authors, AFFI=institutions, JOUR=venues, FSTD=topics
- Influence = sum of citations weighted by 1/(number of authors in cited paper)
- Self-citations and coauthor filtering are ego-relative (depend on entity type being queried)
- The webapp communicates with Konigsberg via `KONIGSBERG_URL` env var (defaults to `http://localhost:8081`)
