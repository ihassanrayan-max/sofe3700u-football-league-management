# Cleanup audit

Date: November 25, 2026  
Baseline: `b3ac6e7` on `main`  
Project: Touchline, SOFE 3700U, Group 20, EPL 2023/24

## Changes

- Reduced the main README from 215 to 89 lines. Removed decorative headings,
  repeated feature descriptions, speculative future work and the obsolete claim
  that `.env.example` defaults to legacy mode.
- Reduced the application guide from 351 to 134 lines. The shared snapshot guide
  remains the installation reference. The application guide now covers runtime
  configuration, accounts, imports, endpoints and legacy upgrades without
  duplicating the full Windows setup.
- Shortened the headers of migrations 06 and 07. Kept their backup, preflight,
  error-handling and implicit-commit instructions. Executable SQL is identical.
- Archived 46 superseded local files outside the Git repository: the old app
  copy, earlier submission exports, old development/test scripts and temporary
  render/output artifacts. Verified every archived file with SHA-256 before
  removing its original copy.
- Removed 4,300 files from the two obsolete Python environments under
  `outputs/Phase_III/.venv` and `work/phase3env`. These dependencies are
  reproducible from the retained requirements files. The active environment
  under `github-public/Phase_III/.venv` was preserved.

## Kept deliberately

- All 20 runtime, template, asset and test source files checked against the
  baseline are byte-for-byte unchanged. No unused application module or function
  was established, so none was deleted on speculation.
- `wsgi.py` imports `services` to register Flask routes. Although its name is not
  otherwise referenced there, removing that import would break the application.
- The legacy importer is still selectable and tested. The migration scripts
  still support existing installations. Neither is dead code.
- The original four Phase II scripts, diagrams, original reporting views and
  current shared database snapshot remain available. Historical dates and
  provenance were retained rather than relabelled.
- Regression tests, provider error handling, quota tracking, library notices and
  required data explanations were retained.
- The active private `.env`, demo password file, API cache, Git history and
  database were preserved. No authorship statements or third-party attribution
  were fabricated or removed.

## Verification performed

- 73 Python tests passed.
- Both JavaScript renderer tests passed.
- `node --check` passed for the application and guest scripts.
- Compared parsed statements before/after both edited migrations: identical SQL
  statements and execution order.
- Compared all tracked `.py`, `.js`, `.css` and `.html` files against the baseline:
  all 20 unchanged.
- `git diff --check` passed. Documentation links and secret exclusions were
  checked before publication.
- The running app's login page returned HTTP 200 after local cleanup.

No new live provider calls or database writes were required for this maintenance
change. The earlier live-import, disposable-MySQL and browser verification is
documented in the application guide; it is not claimed as rerun by this audit.

## Recovery and handoff

The audit machine retains the obsolete-file archive and its hash manifest under
`local_archive/cleanup-20261125` in the workspace, outside `github-public`.
The archive is private and may include old local credentials; do not upload it.
Its former virtual environments can be recreated from requirements if needed.
The previous repository content is also retained in Git history.

Use the current `main` branch or the refreshed Group 20 submission ZIP. Existing
installations only need to pull the code; no SQL reload or migration is required.
The final report, presentation and contribution documents remain separate course
deliverables.
