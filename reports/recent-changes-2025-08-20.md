# Recent Changes — 2025-08-20

## Lead Search Metadata Fixes
- Ensured each result carries accurate search metadata:
  - `search_keyword` = exact term used (e.g., "mexican restaurant", "chinese restaurant").
  - `search_location` = clean City (Title Case), not concatenated phrases.
- Implemented in:
  - `src/providers/multi_provider.py`: annotates every provider result with `search_keyword`, `search_location`, and `full_query`; added robust city cleaner.
  - `src/data_normalizer.py`: enforces city-only Title Case for `Location`; preserves correct `SearchKeyword`.

## Scheduler UX Updates (Scheduling Tab)
- Reordered sections (top → bottom):
  1) Bulk CSV Upload (primary entry point)
  2) Progress bar
  3) Recent Jobs (history)
  4) Scheduled Searches (active schedules)
- Removed the old "Queue Status" table from the visible flow and deprecated the manual “Add Search to Queue” block to streamline CSV-first scheduling.
- Improved instruction panel readability (blue gradient card now contains a light panel with dark text).

## Bulk CSV Scheduling — Expanded Format Only
- Legacy CSV format removed. Only the expanded format is accepted:
  - Required columns: `name`, `keyword` (or `base_keyword`), `location` (or `state`)
  - Defaults assumed (if omitted): `expand=TRUE`, `max_variants=15`, `limit_leads=25`, `verify_emails=false`, `interval_minutes=15`, `interval_hours=0`
- CSV template updated and served dynamically via `/api/schedules/template`.
  - A static `schedule_template.csv` mirrors the same columns for direct download.
- UI upload now targets a cache-safe endpoint: `/api/schedules/bulk-upload-v2`.

## Batch Scheduling Semantics
- When `expand` is TRUE, all expanded variants generated from a single CSV row are treated as one batch and share the same `scheduled_time`.
- `interval_minutes` staggers between batches (rows), not between individual variants within a batch.
- If a batch runtime exceeds the interval, the next batch starts as soon as the runner is free (no artificial idle).

## Combined Export of Results
- New UI block in Scheduler to select recent CSVs and export one combined CSV.
- Endpoints:
  - `GET /api/results/recent` → lists recent CSVs in `output/`.
  - `POST /api/export/combined` → accepts `{ files: [paths...] }` and returns a combined CSV.

## Caching & Template Busting
- Added global no-cache headers to force fresh HTML/JS/CSS on each request.
- Added JS cache-busting to the CSV template download link.

## Operational Notes
- Server expected to run with system Python (no venv). Start with:
  - `python app.py`
- If a prior process is holding port 5000, terminate Python processes before restarting.

## Key Files Edited
- `src/providers/multi_provider.py`
- `src/data_normalizer.py`
- `templates/index.html`
- `app.py`
- `schedule_template.csv`

## New/Updated Endpoints
- `GET /api/schedules/template` → expanded CSV template (with examples)
- `POST /api/schedules/bulk-upload-v2` → bulk upload (expanded format only)
- `GET /api/results/recent` → recent CSVs
- `POST /api/export/combined` → combined CSV export

