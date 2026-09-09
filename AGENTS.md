# Project instructions

- Read `HANDOFF.md` for the current implementation and unresolved source contracts before changing a tab.

- This is the public team implementation repository. Keep collected third-party source, reports, charts, credentials and private workspace files outside it.
- The current deliverable is an independently calculated dashboard, implemented one tab at a time. Keep implementation guides available. Distinguish operational, partial and planned modules; never label a reference snapshot or mock data as live implementation.
- Match each reference chart's axes, series, horizon, benchmark, guides, panels and grouping. Colors need not match. Record undisclosed parameters and unresolved instruments explicitly.
- Run collection and calculation on the user's computer. Keep raw prices and acquisition manifests in the sibling `sangsangin-investment-data/` directory (or SANGSANGIN_DATA_DIR), outside this repository. Publish only code, documentation and compact calculated outputs. Ask the user before large downloads; the collector enforces a conservative 512 MiB local cache budget (explicitly authorized 2026-09-09).
- GitHub Pages serves `docs/` from `main`. All asset links must work beneath the repository subpath.
- Prefer plain HTML/CSS/JavaScript for the current reading/navigation workflow; introduce dependencies only when needed.
- Before publishing, run `python -m unittest discover -s tests`, `python scripts/validate.py`, `node scripts/test_charts.cjs`, `node scripts/test_dashboard.cjs`, and syntax checks for changed JavaScript.
- Extended modules also require `python scripts/validate_extended.py` and `node scripts/test_extended.cjs`. Update generated module documentation with `python scripts/write_status_docs.py` after building snapshots.
- Future quantitative modules must preserve units, benchmark definitions, availability dates, and historical data versions. Do not present unvalidated model claims as verified results.
- Do not add schedules, external messages, trading or paid API usage without explicit authorization.

- User authorized weekday 08:00 and 18:00 Asia/Seoul automated collection, validation and GitHub Pages publication. Use the verified pipeline; do not publish failed or incomplete output.
