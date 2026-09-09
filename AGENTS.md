# Project instructions

- This is the public team implementation repository. Keep collected third-party source, reports, charts, credentials and private workspace files outside it.
- The current deliverable is a static implementation guide, not a live market terminal. Preserve this distinction in UI labels.
- GitHub Pages serves `docs/` from `main`. All asset links must work beneath the repository subpath.
- Prefer plain HTML/CSS/JavaScript for the current reading/navigation workflow; introduce dependencies only when needed.
- Before publishing, run `python scripts/validate.py` and `node --check docs/app.js`.
- Future quantitative modules must preserve units, benchmark definitions, availability dates, and historical data versions. Do not present unvalidated model claims as verified results.
- Do not add schedules, external messages, trading or paid API usage without explicit authorization.
