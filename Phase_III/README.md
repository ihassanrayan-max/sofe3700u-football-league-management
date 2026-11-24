# Touchline — Installation and Execution Guide

Detailed **Windows / PowerShell** instructions for the `touchline-visual-upgrade` branch. See the [main README](../README.md) for features, architecture, and project background.

Run PowerShell commands in your terminal. Run SQL in MySQL Workbench or another connected MySQL SQL editor.

## 1. Install the prerequisites

- **Python 3.11+**, pip, and the Windows `py` launcher.
- A running **MySQL Server 8.0.16+**. Use MySQL, not MariaDB.
- MySQL Workbench or another SQL client. The client alone does not install or start a database server.
- Git and a web browser. VS Code is optional.
- A direct API-Sports/API-Football key with suitable historical-season access for real-data imports.

Check Python in PowerShell:

```powershell
py --version
```

The migration account needs SELECT, INSERT, CREATE, CREATE VIEW, and REFERENCES privileges. The app account needs SELECT/INSERT/UPDATE/DELETE on core tables, SELECT/INSERT/UPDATE on provider tables, and SELECT on the required views and underlying tables. The new views use SQL SECURITY INVOKER.

## 2. Open the correct branch

For a new clone:

```powershell
git clone --branch touchline-visual-upgrade https://github.com/ihassanrayan-max/sofe3700u-football-league-management.git
cd sofe3700u-football-league-management
```

For an existing checkout, open its folder and check:

```powershell
git status
git branch --show-current
```

If already on this branch with a clean working tree, update it using:

```powershell
git pull --ff-only origin touchline-visual-upgrade
```

Resolve local changes or divergent history before updating; do not discard work. Keep your existing `.env`, virtual environment, and database.

## 3. Set up MySQL

The application displays Group 20 but retains the database name **group12_football_phase2** for compatibility.

### Fresh installation

Connect to your MySQL server. Open and execute each entire SQL script in order, checking the output for errors before continuing:

| Order | File | Purpose |
| --- | --- | --- |
| 1 | `01_create_tables.sql` | Creates the schema and core tables |
| 2 | `02_insert_data.sql` | Inserts users, clubs, seasons, players, and fictional sample statistics |
| 3 | `03_create_views.sql` | Creates the ten original reporting views |
| 4 | `Phase_III/05_phase3.sql` | Adds login credentials, web sessions, and legacy import tracking |

**Script 01 drops existing project tables. Only use it for a fresh installation.** Script 02 is not a routine startup command.

Optional: run `04_test_queries.sql` to inspect/check the original seed dataset before imports. Its seed-specific expectations can change after editing data.

The original sample data supports the course database and demo identities. API-Football reports exclude fictional matches, so you do not need to delete the seed data to use the new analytics.

### Existing installation

Do not rerun scripts 01 or 02. Inspect the intended database first:

```sql
USE group12_football_phase2;
SHOW FULL TABLES;
SELECT * FROM v_league_standings;
SELECT COUNT(*) FROM login_credentials;
```

If the Phase III credential/session/import tables are missing, apply script 05. Its CREATE TABLE IF NOT EXISTS statements preserve existing contents.

### API-Football migration — first run only

Keep `TOUCHLINE_PROVIDER=football-data.org` until the migration succeeds. If already fully migrated, skip this section.

1. Stop Flask and every other database writer.
2. Back up the whole schema, including tables, data, views, credentials, and sessions, to a private file outside Git. Use your SQL client's export feature or `mysqldump --result-file`; avoid PowerShell redirection that may produce UTF-16 output. Verify export completion and test restoration only on a separate disposable database/server.
3. Execute `Phase_III/06_api_football_preflight.sql`. This is a read-only checklist; inspect each result.
4. Confirm MySQL version, enabled foreign-key checks, one Premier League competition, the six named clubs, and no existing `provider_*`/`tl_*` objects or Premier League 2023/24 season.
5. Save the baseline counts privately. A standard installation after script 05 has **11 tables and 10 views**. Local backup tables increase this count; identify them instead of deleting them to match a number.
6. Configure the SQL client to **stop execution on errors**. With the database owner's authorization, execute all of `06_api_football.sql` once.
7. On an error, stop and run `ROLLBACK;` in the same connection for any uncommitted data changes. MySQL DDL commits implicitly: earlier CREATE statements and committed data remain. Review the partial state before proceeding; do not blindly rerun the migration.
8. Execute `06_api_football_verify.sql`. Expect **six new tables and fifteen new views**: normally **17 tables and 25 views**. Seasons increase by one and memberships by six; existing matches, players, users, credentials, and legacy links remain unchanged.
9. Verify the new views are readable using the application account. Before imports, most scoped reports are empty and standings show six zero-played teams.

**Fresh-install baseline:** comments in the preflight/verification files mention 30 legacy imports because those checks were originally written for an existing deployment. A fresh seed installation has **zero legacy imports**, which is expected. The migration copies the legacy links that actually exist; importing 30 old matches is not a prerequisite. Compare against your recorded baseline and require zero missing/changed links. Unexpected objects, orphan links, triggers, or partial migrations still need review.

The migration preserves the original ten views and adds six provider tables, five helper views, and ten scoped report views. Do not rerun it to start Flask or update the frontend.

## 4. Install Python dependencies

From the repository root:

```powershell
cd Phase_III
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Skip `cd Phase_III` if your terminal path already ends there. Skip environment creation if `.venv` already exists.

**All remaining PowerShell commands run from Phase_III.** Calling the environment's Python directly means activation is not required.

## 5. Configure .env

Create a private configuration file without overwriting existing values, then generate a random secret:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
```

Open `Phase_III/.env` in your editor. For a successfully migrated API-Football installation, fill in:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=your_existing_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=group12_football_phase2
SECRET_KEY=paste_your_generated_secret_here

TOUCHLINE_PROVIDER=api-football
API_FOOTBALL_KEY=your_direct_api_sports_key
API_FOOTBALL_DAILY_LIMIT=90
FOOTBALL_DATA_TOKEN=
```

| Variable | Meaning |
| --- | --- |
| MYSQL_HOST / MYSQL_PORT | Same server and port as your successful SQL-client connection |
| MYSQL_USER / MYSQL_PASSWORD | Existing MySQL account, not your website login |
| MYSQL_DATABASE | Keep `group12_football_phase2` |
| SECRET_KEY | Stable random value used to sign session cookies |
| TOUCHLINE_PROVIDER | `api-football` after migration; otherwise `football-data.org` |
| API_FOOTBALL_KEY | Direct API-Sports key, not a RapidAPI credential |
| API_FOOTBALL_DAILY_LIMIT | Local rolling 24-hour request cap; default 90, maximum 100 |
| FOOTBALL_DATA_TOKEN | Only used by the legacy football-data.org importer |

Find your MySQL username in the connection settings or run `SELECT CURRENT_USER();` in the SQL editor. For `root@localhost`, use `root`. The example username `group12` is not created automatically.

Obtain a provider account/key from [API-Football](https://www.api-football.com/). Confirm that your account can access league 39, season 2023, and the fixtures, player-statistics, and team-statistics endpoints. The repository does not guarantee subscription coverage.

You can sign in and view already-saved MySQL data without an API key. Uncached provider requests need a valid key. For legacy mode, leave `TOUCHLINE_PROVIDER=football-data.org` and configure `FOOTBALL_DATA_TOKEN` only if importing.

Save the file. Existing process environment variables override `.env`; restart Flask after changes. Keep this file private and out of Git.

## 6. Generate website passwords

On a new installation with the seeded users:

```powershell
.\.venv\Scripts\python -m flask --app wsgi demo-accounts
```

This stores salted password hashes and prints newly generated passwords once. Save them privately.

| Role | Email | Access |
| --- | --- | --- |
| ADMIN | `admin.one@example.com` | Analytics, reports/exports, CRUD, imports |
| USER | `reader.one@example.com` | Analytics and reports/exports |
| GUEST | `guest.one@example.com` | Read-only team directory with name/city filtering |

Rerunning the command preserves existing passwords. If an account produces no output, use its saved password.

For deliberate recovery of **all three existing demo passwords**:

```powershell
.\.venv\Scripts\python -m flask --app wsgi reset-demo-passwords
```

Run this only when you intend to replace all three passwords. It requires an interactive local terminal without output redirection, validates the expected identities, and displays the new passwords once. It is not a routine startup step.

## 7. Start and open the application

```powershell
.\.venv\Scripts\python -m flask --app wsgi run --host 127.0.0.1 --port 5000
```

Open **http://127.0.0.1:5000/login**, then use a demo email and its generated password.

Leave the terminal running. Press **Ctrl+C** to stop. For subsequent runs, start MySQL if needed and use the same Flask command; do not recreate tables or credentials.

After code/configuration changes, restart Flask and press **Ctrl+Shift+R** in your browser to reload the frontend. This starts a local development server, not production hosting.

## 8. Import real fixtures and statistics

These steps require ADMIN, the completed migration, and API-Football mode.

1. Open **Fixture Imports**.
2. Choose **Six-club fixtures**, then **Fetch preview**.
3. Review returned clubs, dates, status, and scores. Click **Save preview** to write the snapshot to MySQL.
4. Choose **Next 2 fixtures: players + statistics**, then fetch and save that preview.
5. Repeat enrichment batches while completed fixtures remain pending and quota allows.
6. Inspect saved history and **Team statistics**, then revisit Overview and player reports.

The importer requests `/fixtures?league=39&season=2023`, followed by `/fixtures/players` and `/fixtures/statistics` for up to two saved completed fixtures per enrichment batch.

A preview does not save imported records to MySQL, but can consume quota and write cache/session state. API-Football snapshots expire after **one hour**; saving uses that exact snapshot without refetching. Expired/mismatched previews require a fresh preview.

Successful responses cache for **seven days** in ignored `work/api-football.sqlite3`. The file also records the rolling 24-hour budget and ten-requests-per-minute limit. Failed calls consume budget. A complete 30-match enrichment normally requires 61 calls before extra cache misses or errors. Other applications using the same key consume provider quota too; adjust the local allowance accordingly. Do not delete the ledger to bypass limits.

### Data scope and interpretation

- Both clubs must be among Arsenal, Chelsea, Liverpool, Manchester City, Manchester United, and Tottenham Hotspur.
- A full home/away schedule for the subset has 30 fixtures; no records are invented to meet this count.
- Standings represent a six-club mini-league, not the official EPL table.
- Player totals cover only imported appearances from those fixtures, not all 38 league games.
- Enrichment is separate from fixture import. Player reports may be empty until it is saved.
- Unknown values remain NULL; explicit zero stays zero. Missing/zero minutes do not generate invented appearances.
- Synthetic/legacy records stay in the database but are excluded from new-mode analytics.
- Imported historical profiles/statistics use separate provider tables; the original player CRUD form does not manage them.
- Switching the provider flag back to `football-data.org` restores legacy report scope without deleting new data. Legacy analytics can include fictional seed records.

## 9. Verify the installation

1. ADMIN: inspect Overview, Match Centre, all ten reports, filters, and CSV/PDF exports.
2. ADMIN: inspect Data Workbench; test writes with disposable records in a suitable test database.
3. ADMIN: check saved imports and available player/team enrichment.
4. USER: confirm analytics/exports work and management/import pages are denied.
5. GUEST: confirm only the team directory appears; search/filter works and analytics/report/export routes are denied.
6. Sign out and check protected API requests require authentication.

Automated checks from `Phase_III`:

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Optional JavaScript syntax checks, with Node.js installed:

```powershell
node --check static/ui.js
node --check static/guest.js
node --check static/chart.umd.min.js
```

The suite uses mocks and isolated in-memory data. It does not establish live MySQL migration success, API subscription access, or browser layout quality on your machine.

## REST API reference

| Endpoint | Method | Access and purpose |
| --- | --- | --- |
| `/api/login`, `/api/logout` | POST | Start/end a session |
| `/api/teams?q=...&city=...` | GET | Authenticated team directory; basic team fields only |
| `/api/reports/{view}` | GET | ADMIN/USER; JSON/CSV/PDF, optional q, field, format |
| `/api/records/{table}` | GET, POST | ADMIN; list/create core records |
| `/api/records/{table}/{key}` | GET, PUT, DELETE | ADMIN; read/update/delete a core record |
| `/api/import/preview` | POST | ADMIN; preview fixtures or enrichment |
| `/api/import/save` | POST | ADMIN; save snapshot with its preview_id in API-Football mode |
| `/api/import/history` | GET | ADMIN; saved imports |
| `/api/import/statistics?match_id=...` | GET | ADMIN; saved team statistics in API-Football mode |

Writes require the session CSRF token in `X-CSRF-Token`; the interface supplies it. Composite record keys use comma-separated primary-key values. Backend allowlists constrain table/view names and query values use bound parameters.

## Troubleshooting

| Problem | Resolution |
| --- | --- |
| Cannot find Phase_III/Phase_III | You are already in Phase_III; skip the cd command. |
| py not recognized | Install Python with its launcher, then reopen the terminal. |
| Virtual-environment Python not found | Check the directory and create .venv in step 4. |
| Module not found | Install requirements with the virtual environment's Python. |
| MySQL connection refused | Start MySQL Server and check host/port. |
| MySQL access denied | Correct database credentials/permissions, not the website password. |
| Unknown database | Initialize the schema on the server configured in .env. |
| Missing login_credentials/web_sessions | Apply script 05 to the correct database; do not rerun script 01. |
| Missing tl_* or provider_* object | Provider mode was enabled before complete migration; return to legacy mode and review migration state. |
| Object already exists in script 06 | Stop and review an existing/partial migration; do not drop objects or blindly rerun. |
| Demo command prints no passwords | Credentials exist; use saved passwords or deliberately reset them. |
| Port 5000 in use | Stop the old Flask process, or use --port 5001 and browse to that port. |
| Import authentication/coverage error | Check the direct API-Sports key and season/endpoint subscription access. |
| Quota/rate-limit error | Wait for the allowance window, check provider usage, and preserve the local ledger. |
| Player reports empty | Save enrichment after fixtures; coverage may also be absent. |
| Guest sees no analytics | Expected: Guest can only use the team directory. |
| Old design or configuration | Restart Flask, hard-refresh, and check process variables overriding .env. |

Keep API keys, passwords, database dumps, generated credentials, and cache files out of Git. Another contributor's successful migration or import does not establish the state of your own installation.

### Known player subtotals (migration 07)

Player Totals and Recorded goal leaders sum available numeric statistics across
qualifying imported appearances. SQL SUM ignores NULL but leaves all-NULL groups
NULL; explicit zero remains zero. Goal and assist coverage are independent.
Complete observed coverage means all qualifying imported appearances have a
numeric value, not that the full season has been enriched. CSV includes the four
coverage columns; PDF includes those columns and a partial-season explanation.

For an existing database, apply only migration 07, not migration 06:
1. Keep a current private backup and pause imports/manual edits while comparing
   preflight and verification results. Finish any open Workbench transaction.
2. Connect in MySQL Workbench using an authorized account. Set
   group12_football_phase2 as the default schema.
3. Open and run 07_player_totals_preflight.sql. Require database_matches=1,
   MySQL 8, the four expected views, and no duplicate appearance keys.
   Review the existing view definition and save the counts for comparison.
   The account needs CREATE VIEW, DROP on the targeted view, and SELECT on its
   dependencies. If permissions are missing, stop and ask the database owner;
   do not broaden the Flask account privileges.
4. Open 07_player_totals.sql, review it, then execute that file alone.
   Its only schema change is CREATE OR REPLACE of tl_v_player_totals with
   SQL SECURITY INVOKER. It is repeatable and implicitly commits; it does not
   insert, update, delete, or rebuild table records or original Phase II views.
5. Run 07_player_totals_verify.sql. Require zero mismatch rows, unchanged
   source counts/sums, and all ten original views. Review partial subtotals.
6. Restart Flask for the updated export text and hard-refresh the browser.
   Check Player Totals, its CSV/PDF exports, and Recorded goal leaders.
   Unknown totals should remain blank in exports and a dash on screen.
   Guest report access must still return 403.

Migration 07 has not been executed automatically. Fresh installations use the
updated canonical view in 06_api_football.sql; existing installations use 07.
No API requests or additional imports are needed to recover known subtotals.
Additional enrichment is a separate, quota-consuming action.

Offline regression commands from Phase_III:
- python -m unittest discover -s tests -v
- node --test tests/player_totals_ui.test.js
- node --check static/ui.js
- node --check static/guest.js
