# Touchline application guide

Group 20, EPL 2023/24. For a new installation, use the
[teammate setup guide](../setup/fresh_database/README.md). Do not combine its
snapshot with the original seed scripts or migrations.

## Configuration

Create a private `.env` from `.env.example` in this folder. Set the MySQL host,
port, user and password for your own server. The shared installation uses
`MYSQL_DATABASE=touchline_clean_20261124` and `TOUCHLINE_PROVIDER=api-football`.
Generate a stable random `SECRET_KEY`. Add your own direct API-Sports key as
`API_FOOTBALL_KEY` for uncached imports. Saved records can be viewed without it.
`API_FOOTBALL_DAILY_LIMIT` defaults to 90; the local ledger also limits requests
to ten per minute and never exceeds 100 in a rolling day.

Workbench executes SQL and selects database connections. It does not set Flask
environment variables. Existing process variables override `.env`; restart
Flask after changing configuration. Legacy installations retain their own schema
and provider settings. The old `group12_football_phase2` identifier does not
change the current Group 20 branding.

## Accounts and access

From this folder, run:

```powershell
.\.venv\Scripts\python.exe -m flask --app wsgi demo-accounts
```

This provisions salted hashes for the existing demo identities and prints each
new password once. Repeated runs preserve existing passwords. The accounts are
`admin.one@example.com` (ADMIN), `reader.one@example.com` (USER) and
`guest.one@example.com` (GUEST). Administrators manage records and imports;
users browse/export reports; guests see the team directory only.

To deliberately reset existing demo passwords, run `reset-demo-passwords`
in an interactive local terminal. Do not redirect its output. Logout revokes
the server-side session. Password changes revoke that user's sessions.

## Reports and exports

Report Studio defaults to the active 2023/24 dataset. Select **Phase II archive**
and click **Apply filter** to execute the original ten `v_*` views. The active
reports execute `tl_v_*` views. Search uses parameterized MySQL queries; JSON,
CSV and PDF share the selected source and filter. Sorting a displayed HTML table
is a browser operation, so its row order may differ from an exported file.

The archive preserves historical dates and fictional sample records. The active
standings cover six clubs; unknown goals/assists stay distinct from zero. Player
totals sum known values and display independent goal/assist coverage counts.
Complete observed coverage does not mean a complete season.

## API imports

API-Football requests go to `https://v3.football.api-sports.io/` using the server's
key. Fixture previews request league 39, season 2023. Only matches between the
six project clubs qualify. Enrichment requests player/team statistics for up to
two saved, completed fixtures missing enrichment.

Fetch preview validates the response and stores a one-hour preview. Save requires
that preview's ID, uses its cached contents and writes in a MySQL transaction.
Provider mappings and fixture checks prevent duplicates; conflicting existing
results are rejected. Saved imports and team statistics are retrieved from MySQL.
Missing values remain unknown. No background polling or automatic imports run.

Responses and a shared local quota ledger are stored in `work/api-football.sqlite3`.
Keep that file private and preserve it when updating code. Do not remove the
ledger to bypass provider limits. Cached previews are not new live requests.
The optional legacy mode uses `TOUCHLINE_PROVIDER=football-data.org` and
`FOOTBALL_DATA_TOKEN` for the preserved 2025/26 fixture importer.

## REST endpoints

- `POST /api/login`, `POST /api/logout`: session login/logout.
- `GET /api/teams?q=...&city=...`: authenticated team directory.
- `GET /api/reports/{view}`: ADMIN/USER reports. Parameters: `dataset=active|phase2`,
  `q`, `field`, and `format=json|csv|pdf`.
- `GET, POST /api/records/{table}`: ADMIN list/create.
- `GET, PUT, DELETE /api/records/{table}/{key}`: ADMIN read/update/delete.
- `POST /api/import/preview`: ADMIN fixtures or enrichment preview.
- `POST /api/import/save`: ADMIN save using `preview_id`.
- `GET /api/import/history`: ADMIN saved imports.
- `GET /api/import/statistics?match_id=...`: ADMIN saved team statistics.

Writes require `X-CSRF-Token`; the frontend supplies it. Composite record keys
use comma-separated primary-key values. IDs, tables, views and fields are
validated, and query values are bound parameters. Typical responses are 400 for
invalid input, 401 for login, 403 for permissions, 409 for record conflicts,
429 for quotas, 502 for provider failures and 503 for database/configuration errors.

## Existing legacy installations

The current snapshot already contains the final schema and views. Do not run
these migrations against `touchline_clean_20261124`. The scripts explicitly use
the older `group12_football_phase2` schema.

For an existing legacy schema, stop writers and take a private backup before
DDL. Disable continuation after SQL errors in Workbench. Apply 05 only if the
credential/session tables are missing. For migration 06, run its preflight and
require the provider/helper objects and EPL 2023/24 season to be absent; then
run 06 once and its verification script. It adds six tables and fifteen views.
Compare legacy mappings against your own baseline, not a fixed import count.
For the player-totals correction on a migrated schema, use the 07 preflight,
07 view update and 07 verification scripts. Migration 07 only replaces that view.

Stop on any error. Roll back uncommitted DML in the same connection; MySQL DDL
commits implicitly and is not undone by rollback. Inspect partial migrations
before retrying. Never rerun the original schema-reset script on a working database.

## Troubleshooting

- Connection refused: start MySQL and check the configured host/port.
- Access denied: check the account's credentials and access to the selected schema.
- Missing tables/views: verify the schema and installation path; do not mix scripts.
- No printed demo passwords: credentials already exist; use your saved passwords.
- Provider error: check the key, historical season access and remaining quota.
- Empty player reports: enrichment may not be loaded or available for those fixtures.
- Port 5000 occupied: stop the older Flask instance or select another local port.
- Old page/configuration: restart Flask, hard-refresh and check the checkout folder.

## Verification

The November 24 audit passed 73 Python and two JavaScript tests. Disposable MySQL
checks covered both report datasets and exports, all eight CRUD lifecycles,
roles and error cases. One real fixture request returned 30 eligible matches;
four enrichment requests returned player/team statistics for two fixtures.
Preview/save/reimport preserved unique mappings. Headless Edge exercised the
report tables, charts, filtering, downloads, AJAX CRUD, import history, mobile
layout and logout. Test schemas were removed; live football records were unchanged.

These results describe the tested configuration at that time. Each teammate
must supply valid local credentials; provider access can change. The current
cleanup verification is recorded in [CLEANUP_AUDIT.md](../CLEANUP_AUDIT.md).
