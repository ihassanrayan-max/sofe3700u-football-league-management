# Touchline | Group 20

## API-Football 2023/24 integration

### Current deployment status — reported by the project owner

The owner confirmed the migration completed with 17 tables and 25 views, preserving all 30 original football-data.org imports. All 30 eligible EPL 2023/24 fixtures were imported. Live player-statistics imports and dashboard goal leaders were tested successfully. Further enrichment is temporarily paused by the local API quota; keep the quota ledger intact and resume batches when the allowance permits. These live results are owner-reported, not repeated during Git publication. Do not rerun the first-run migration on this configured database.

The setup and review notes below document the initial preparation and remain instructions for a fresh, unmigrated installation. `.env.example` deliberately defaults to legacy mode until a new installation has applied the migration; the configured deployment selects `TOUCHLINE_PROVIDER=api-football` privately.

The new integration uses API-Football v3 (direct API-Sports), league 39, season 2023. It retains only matches where **both** clubs are Arsenal, Chelsea, Liverpool, Manchester City, Manchester United or Tottenham Hotspur. Standings are a six-club **mini-league**, not the official 20-club EPL table. The completed six-club schedule normally contains 30 fixtures; no rows are manufactured to meet that count.

**Initial preparation note (superseded by the deployment status above): the implementation itself did not migrate or change the existing database.** Until the reviewed migration is approved and applied, leave `TOUCHLINE_PROVIDER=football-data.org` (also the default when absent). Existing 2025/26 routes remain operational in that mode. Do not change the provider flag early: new-mode reports need the new views. There is no automatic migration or background import.

### Migration review — November 20, 2026

**Verdict: additive and suitable for controlled first-run execution after the checks below, but not yet live-validated. No migration or live database change was performed during this review.**

Fixed three INSERT statements that selected their target table in subqueries, which MySQL restricts. Season ID allocation now happens in a separate session-variable SELECT while all writers are stopped; the migration resolves the competition and club IDs by name, not assumed local IDs. Plain CREATE rejects existing provider table/view names instead of silently accepting incompatible tables or replacing views. All three data additions are in one transaction. No existing match, player, statistic, credential, session or user row is updated or deleted. Six provider tables and fifteen views are created in FK/dependency order, with matching signed INT references and restrictive delete behavior. Original ten view definitions remain untouched; their *results* can change when the new season/memberships are added (the original standings view gains six zero-played rows).

The private backup at `C:\Users\herae\Documents\Touchline_Backups\touchline_before_api_football.sql` exists: 75,542 bytes, **UTF-16**, 11 expected InnoDB tables, 10 final view definitions, 11 balanced INSERT statements and a terminal dump-completed marker. All eleven table column/type sets and eleven FK structures match repository definitions. Counts: competitions 6, seasons 6, memberships 6, clubs 6, players 12, matches 42, player stats 24, legacy imports 30, users 6, credential rows 3, session rows 1. These are backup-time counts, not a fresh live audit. No credential values or row contents were printed or copied into the repository.

Backup SHA-256: `a9d628f494a9556956f79aa671f72d468d5072dadca78b69fa6c114a07c5b7e3`.

**Backup limitation:** structural checks and a checksum do not prove restorability. MySQL documents that PowerShell-redirection UTF-16 dumps cannot be loaded correctly as-is. Preserve this file. Before migration, obtain a separate correctly encoded export using Workbench Data Export or `mysqldump --result-file` (never overwrite this backup and never put a password on the command line). Verify the new file, and test restoration only in a separately approved disposable schema/server; dumps can contain USE and DROP statements targeting the original schema. Neither conversion nor restoration was performed here.

Exact Workbench procedure, for execution only after approval:

1. Stop Flask and every other writer. Keep `TOUCHLINE_PROVIDER=football-data.org`. Confirm backup readiness as described above.
2. Open **Edit → Preferences → SQL Editor → SQL Execution** and uncheck **Continue on SQL script execution on errors (by default)**. Apply this before opening a fresh connection. Verify the current connection's continue-on-error setting is off too. Keep the connection dedicated to this migration; query tabs on one connection share transactions.
3. Connect to the intended local MySQL server using your existing authorized migration account. Open **File → Open SQL Script → `06_api_football_preflight.sql`**. Execute that read-only file (Ctrl+Shift+Enter with no partial selection). Review every result and its comments: correct schema; MySQL >=8.0.16; FK checks enabled; 11 base tables/10 views; no provider_* or tl_* names; no EPL 2023/24 season; exactly the six clubs and one English Premier League competition; 30 legacy links in 2025/26; no orphan links; no unexpected triggers. Save the baseline counts privately. Stop on any discrepancy. The administrator must have sufficient metadata privileges to see triggers and all objects.
4. Open **`06_api_football.sql`** in its own tab. Reconfirm its `USE group12_football_phase2` line. Only now, after approval, execute the whole file with Ctrl+Shift+Enter. Watch **Action Output**. On the first error, stop and issue `ROLLBACK;` in the same connection to cancel any still-uncommitted data additions. Do not continue, rerun, drop created objects or restore over the live schema automatically. DDL has implicit commits, so rollback cannot undo earlier CREATE statements or already committed data additions.
5. If there were no errors, open and execute **`06_api_football_verify.sql`**. Expect 17 base tables and 25 views; unchanged original row counts except seasons +1 and memberships +6; 30 matching legacy namespace links and no API-Football links yet. All ten original and ten scoped report queries must execute. New scoped reports are empty except six zero-played standings rows. Repeat scoped SELECT checks using the application's account to verify SQL SECURITY INVOKER permissions.
6. Stop here if only migration was authorized. Activating the provider and saving API imports are separate subsequent steps; they create new records. Do not run Phase II scripts, credential commands or a backup restore against the project database.

Offline checks: 47 unittest cases passed, including six migration review cases. Three portable INSERT statements were tested against fictional test rows in an isolated **in-memory SQLite database**, checking non-assumed IDs, preservation and duplicate rejection; this is not a MySQL migration rehearsal. JavaScript syntax passed. No live MySQL connection or provider request was made. MySQL view compilation, server permissions, metadata drift since backup and an actual backup restoration remain unverified.

Sources: [MySQL INSERT/SELECT restriction](https://dev.mysql.com/doc/refman/8.0/en/insert-select.html), [implicit commits](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html), [dump encoding](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html), [Workbench execution preferences](https://dev.mysql.com/doc/workbench/en/wb-preferences-sql-editor.html).

### Safe activation steps — only after approval

1. Stop Flask and other writers. Use an authorized MySQL administrator to back up **the entire existing `group12_football_phase2` schema**, including data, all original views, login credentials and sessions. Keep the dump outside Git in a private folder. In MySQL Workbench use **Server → Data Export**, select the existing schema and all objects, and export to a self-contained file. Verify the export completed and test restoration only into an approved separate schema. A dump contains sensitive account hashes and session data; do not upload it.
2. Record baseline counts and IDs for `matches`, `imported_matches`, `players`, `player_match_stats`, `teams`, `users`, `login_credentials`, and the ten original views. Confirm the expected 30 football-data.org mappings, six named clubs and Premier League competition. This is now a first-run migration: if any provider_* / tl_* objects or the EPL 2023/24 season already exist, stop for separate review; do not rerun or overwrite them.
3. Review **`06_api_football.sql`**. After explicit approval, execute only this file in Workbench against the existing schema. Do **not** rerun scripts 01–04 or any password command. MySQL DDL commits implicitly, so the whole migration is not transactionally reversible. Migration permissions include SELECT, INSERT, CREATE, CREATE VIEW and REFERENCES. The migration deliberately uses plain CREATE, not IF NOT EXISTS or OR REPLACE: existing names cause an error. All added views use SQL SECURITY INVOKER, so the app needs SELECT on their underlying tables/helper views too. Resolve any failure before activating the application; do not retry the complete script blindly.
4. This additive migration creates six tables: `provider_teams`, `provider_matches`, `provider_players`, `provider_player_stats`, `provider_team_stats`, `provider_enrichment`. It copies legacy match links into the `football-data.org` namespace without changing `imported_matches`. It adds a separate 2023/24 season and six memberships, five scoped helper views, and ten `tl_v_*` report views. It does not alter or remove original tables, rows, credentials, matches, player assignments, or the ten original `v_*` views. Verify baseline records remain unchanged, the new season has exactly six memberships, and all 25 original/new views are readable. The existing app account needs SELECT/INSERT/UPDATE on the added tables and SELECT on the new views.
5. In the private `Phase_III/.env`, add `API_FOOTBALL_KEY` with your direct API-Sports key and set `TOUCHLINE_PROVIDER=api-football`. Keep the database name and other credentials unchanged. `API_FOOTBALL_DAILY_LIMIT=90` is the conservative default, capped at 100. Existing process environment values take precedence over `.env`. Restart Flask.
6. Sign in with the existing ADMIN account. In Fixture imports choose **Six-club fixtures → Fetch preview**. Review the real returned data, then **Save preview**. Preview alone does not write to MySQL. Save uses that exact server-side snapshot, valid for one hour, without a second API request. Conflicting existing fixtures stop the entire transaction for manual review; they are not silently overwritten.
7. Choose **Next 2 fixtures: players + statistics**, preview and save each batch. This requests `/fixtures/players` and `/fixtures/statistics` for at most two already saved, completed fixtures. Repeat until no pending fixtures remain. A full 30-match dataset normally requires 61 calls (one fixture list plus two calls per fixture), spread over explicit batches. A cold fixture cache adds one call to a batch. **The team-statistics endpoint has not been live verified in this task.** Provider errors stop the batch with an actionable message; successful empty coverage is recorded as empty, never replaced with fake values. Saved history exposes the returned player/team counts and a **Team statistics** button.
8. Verify all ten reports, filters, CSV/PDF exports, dashboard totals, guest/user restrictions and CRUD in an approved test environment. Check that new reports contain only linked non-fictional 2023/24 fixtures. Confirm the original 30 imported matches and all historical records remain unchanged. Switching the flag back to `football-data.org` restores the old application scope without deleting the new data.

### Data contracts and limitations

- `/api/import/preview`, `/save`, `/history` and all existing report/CRUD URLs are preserved. New preview JSON accepts `kind: fixtures` or `kind: enrichment`. Save must send the returned `preview_id`; a mismatched tab or expired preview is rejected. ADMIN, session and CSRF enforcement remain in place. `/api/import/statistics?match_id=...` reads saved team statistics for ADMIN.
- Provider IDs are independent from local IDs. Match identity is provider + external ID, with a second check of season + home club + away club. EPL clubs meet once per home/away pairing each season. A matching cross-provider fixture is reused; differing kickoff, result or ambiguous candidates require manual reconciliation. A 2025/26 fixture can never match a 2023/24 fixture.
- Historical player identities are provider + external player ID + club, with independent local IDs in `provider_players`. The same player can have multiple historical club memberships. These IDs are not IDs in the original `players` table. Original eight-table CRUD remains available; imported historical profiles/statistics are managed by the provider importer, not the original player editor. Provider-mapped matches cannot be edited/deleted through CRUD in new mode.
- Match player records store nullable minutes, goals, assists and raw returned statistics as JSON. Unknown stays NULL; explicit zero remains zero. Zero-minute substitutes are retained but excluded from appearance reports. Profiles with unknown minutes do not contribute an invented appearance. Season player totals are NULL when any included appearance is missing that measure; unknown goal totals are omitted from the leaderboard. Own goals can make player-goal sums lower than team scores. No missing assists are inferred as zero.
- Player totals cover only imported appearances in six-club matches, not all 38 league games. `/players/topscorers` is intentionally not used to populate these totals: its league-wide aggregates cannot be attributed to individual matches or to this subset. Profiles and per-match goals/assists come from `/fixtures/players` instead. Further raw player statistics are retained in `provider_player_stats.details`; the original ten reports expose their established columns.
- All original `v_*` views still include the untouched Phase II/history dataset for course review. In new mode the same ten HTTP report routes query `tl_v_*` equivalents with the same column contracts. Fictional records are excluded before aggregation, including home/away and player reports. Historical records remain visible in ADMIN's original Data Workbench. Scheduled fixtures and player reports may legitimately be empty; never seed fake rows to fill them.
- Cache/quota state lives in ignored `Phase_III/work/api-football.sqlite3`, shared by local Flask workers. Successful responses cache for seven days; preview snapshots for one hour. Failed calls consume the local budget. The ledger enforces a rolling 24-hour cap and ten requests/minute; no automatic retries. Do not delete the ledger to bypass limits. Other tools using the same API key also consume quota: check the provider dashboard and reduce the local limit to the remaining allowance. Provider exhaustion headers/HTTP 429 block fresh calls conservatively for 24 hours. Cached responses can still be reviewed. This is a single-host cache, not a distributed quota coordinator.

Provider contracts: [official API-Football v3 documentation](https://www.api-football.com/documentation-v3). No new Python dependency is required; SQLite is used only for the local cache, not as a replacement for MySQL.

### Verification for this change

Current offline result: **48 tests passed**; `node --check static/ui.js` passed. Run `python -m unittest discover -s tests -v` from Phase_III and `node --check static/ui.js`. Tests use isolated provider responses, mock MySQL operations and temporary SQLite cache files. Workspace route tests isolate their cache from the local application ledger: a missing key with absent/expired cache returns an actionable 503, while a valid cached fixture response still produces a successful preview without network access or quota reservation. They do not connect to or alter MySQL and do not consume API quota. They cover parsing, null/zero stats, namespace/club mapping, cross-provider matching, repeated imports, transaction rollback, quota/caching, all ten report routes, permissions, templates and CSV/PDF signatures. Live API access, migration execution, SQL-view results against MySQL and post-migration browser workflows remain unverified until approved. Historical audit results below concern earlier versions, not this provider switch.

## Historical setup and audit notes (football-data.org mode)

Football League Management and Statistics System · SOFE 3700U · Fall 2026

Touchline is a local Flask application for the six-club 2025/26 Premier League database. PyMySQL runs the original ten views, vanilla JavaScript handles forms and tables, Chart.js draws the standings, and ReportLab generates PDF tables. The four original SQL scripts are in the parent directory.

## Windows setup

1. Use Python 3.11 or newer, PowerShell, and an existing reachable MySQL 8.0.16+ server. Open the Phase_III directory in PowerShell.
2. In Workbench connect to the existing database. Check it with the following commands.

~~~sql
USE group12_football_phase2;
SHOW FULL TABLES;
SELECT * FROM v_league_standings;
~~~

3. Only after approving the schema change, run **05_phase3.sql** on that connection if the Phase III tables are missing. It adds login_credentials, imported_matches and web_sessions. Running it again preserves their contents. **01_create_tables.sql resets Phase II tables.** Use scripts 01, 02 and 03 in order only when initializing an empty, separate demonstration database before migration. Script 04 checks the original seed dataset.
4. The migration account needs CREATE and REFERENCES privileges. Configure a local app account with SELECT, INSERT, UPDATE and DELETE on the project schema and access to all ten views. Use your course database credentials.
5. Create the environment and install dependencies.

~~~powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
~~~

6. Paste the generated value into SECRET_KEY in .env. Set MYSQL_HOST, MYSQL_PORT, MYSQL_USER and MYSQL_PASSWORD for your connection. Keep MYSQL_DATABASE set to group12_football_phase2. Set FOOTBALL_DATA_TOKEN to your football-data.org v4 token for the import demonstration. Restart Flask after changing .env. Keep this local file private.
7. Only after approving credential writes for all three accounts, provision the three existing demo identities. The command creates a salted password hash for each account without credentials, commits the changes and prints its generated password once. Save those passwords for the demo. Repeated runs preserve existing passwords.

~~~powershell
.\.venv\Scripts\python -m flask --app wsgi demo-accounts
.\.venv\Scripts\python -m flask --app wsgi run --host 127.0.0.1 --port 5000
~~~

8. Open **http://127.0.0.1:5000/login**. Use the password printed for the corresponding address. If no password is printed for an account, it already has a credential: use its previously saved password. This command cannot recover or reset it. Successful sign-in writes a session to web_sessions and removes expired sessions.

| Role | Seed account | Access |
|---|---|---|
| ADMIN | admin.one@example.com | All reports, exports, eight management forms and provider import |
| USER | reader.one@example.com | Dashboard, all ten reports, search and exports |
| GUEST | guest.one@example.com | Completed results and scheduled fixtures |

Role checks load the current user from MySQL for each protected request. Sessions use a signed HttpOnly cookie with a four-hour lifetime. Forms send a session CSRF token. Logout revokes the session in MySQL and clears its cookie. Admins can set a new password from the Users form.

## Demonstrate the application

1. Sign in as ADMIN. Dashboard displays points by club from v_league_standings and completed games from v_match_results. The standings combine fictional and imported matches. They describe the course dataset.
2. Open Report studio. Select each report in order. The selector follows Phase II views 1–10. Column headings come from the view. Select Match Results, choose Home Team, enter Arsenal and click Apply filter. Download CSV and PDF and compare the records with the table. Queries use SQL LOCATE for literal substring searches. Change the field to kickoff time to search by date prefix.
3. Open Data workbench. Select a table to see its records and required fields. IDs are explicit, as in Phase II. Try an unused team ID and a fictional club name. Create the club, edit its city and delete it. Repeat with a test player linked to an existing team. Test a duplicate ID and a referenced club deletion. A conflict keeps the existing rows. To edit a composite membership or stat key, select its original row first. Blank password on edit keeps the current hash.
4. Create a synthetic match between two different enrolled clubs inside the season dates. Scheduled matches require blank scores. Complete it with two scores, add a player stat from a participating club, and verify the results and standings. Try a player from a third club or goals above the team score. Delete your stat before deleting its match. Manual match and statistic creation uses the Phase II synthetic defaults.
5. On Fixture imports click Fetch preview. Review both clubs, kickoff, status and score. Click Save preview and reload the page. Saved imports reads the database. Repeat preview and save to verify provider IDs stay unique. To demonstrate error handling, temporarily remove the token locally and restart the app.
6. Sign out, sign in as USER, open reports and export. Visit /manage to see the admin restriction. Sign in as GUEST and verify that only results and fixtures are available. Visiting /api/reports/v_league_standings as GUEST returns 403. After logout a protected API request returns 401.
7. Capture the ten report tables and demo outcomes for the group's final report. The assignment calls for a 10–12 page final report, contributions, a 5–7 minute presentation and a two-minute Q&A. Record the group's own live results and contributions.

## REST endpoints

| Route | Methods | Purpose |
|---|---|---|
| /api/login, /api/logout | POST | Start or end a session |
| /api/reports/{view} | GET | JSON columns and rows. Optional q, field and format=json/csv/pdf |
| /api/records/{table} | GET, POST | List or create records as admin |
| /api/records/{table}/{key} | GET, PUT, DELETE | Read, replace or delete one record. Composite keys use comma-separated IDs in primary-key order |
| /api/import/preview, /api/import/save | POST | Fetch eligible provider fixtures and save the reviewed data |
| /api/import/history | GET | List saved provider fixtures |

Send JSON objects for writes, including all editable fields for POST and PUT. All mutations require the X-CSRF-Token supplied to the signed-in page (also available on the login page). The interface sends it automatically. The backend restricts table, view and column identifiers to known names and binds SQL values. Typical errors are 400 for validation, 401 for login, 403 for permissions, 409 for constraint conflicts, and 503 for database or credential configuration.

## Provider data and persistence

The server requests GET /v4/competitions/PL/matches?season=2025 with X-Auth-Token. Historical access depends on the token's plan. See the [competition match filters](https://docs.football-data.org/general/v4/competition.html) and [rate limits](https://docs.football-data.org/general/v4/policies.html). Only fixtures between two of Arsenal, Chelsea, Liverpool, Manchester City, Manchester United and Tottenham qualify. The mapping uses provider club IDs and checks the original named season memberships in MySQL. FINISHED requires two full-time scores. TIMED and SCHEDULED keep blank scores. In-progress, postponed and incomplete fixtures are skipped. An empty eligible response produces an error.

Saving fetches again and compares the eligible records with the preview fingerprint. A change requires a fresh preview. In one transaction the app inserts new matches with is_synthetic=0 and records the unique provider ID, or updates the existing match linked to that ID. A fixture-key conflict rolls back the batch, preserving the existing sample. Imported rows are managed through the import page. History runs SELECT against imported_matches joined to v_match_details. Manually entered player statistics remain fictional, including those for imported fixtures.

## Final audit · November 18, 2026

The configured project database returned rows from all ten views. Write tests used a separate MySQL database built with the original four scripts and the additive migration. The audit removed that database after testing.

| Feature | Verification | Status |
|---|---|---|
| Authentication and roles | Session sign-in, logout, rejection of reused logged-out cookie, missing CSRF token, and guest/user restrictions | Passed |
| Validation and CRUD | All eight entities passed create, read, update and delete. Edge submitted changes and blocked an empty form. Backend rejected invalid input and deletion of referenced records | Passed |
| REST and AJAX | Edge exercised the four HTTP methods on the team management page | Passed |
| Reports and charts | All ten views returned rows from MySQL. Edge checked table headings and row counts against each response and rendered a six-club chart | Passed |
| Search and exports | Filtered by home club in SQL, downloaded both formats from Edge and checked filtered CSV rows and PDF contents | Passed |
| Import workflow | Controlled provider response passed browser preview/save and reload. Repeated import updated the score under the same external ID. Test records stayed in the disposable database | Passed |
| Live provider access | Authenticated 2025/26 response returned 30 eligible six-club fixtures; preview, save and history succeeded in a disposable MySQL schema | Passed |
| Error handling | Missing token, simulated provider throttling and database outage, invalid input and dependent deletes | Passed |
| Windows installation and compatibility | Installed dependencies, ran Flask, replayed Phase II scripts in an isolated schema and applied the migration | Passed |

The disposable test schema was removed after the audit. For the final demonstration, capture screenshots using your own project database. The 10–12 page final report, 5–7 minute presentation slides, contribution matrix and team evaluation are separate course deliverables; this source package does not include completed versions of them.


## Touchline redesign · November 19, 2026

The workspace now uses a responsive navigation rail, a dedicated sign-in layout, club monograms, a season overview, and a match centre. All production screen data comes from the existing protected REST endpoints; no demonstration responses are embedded in the application.

- **Overview:** select a standings season to update the table, points chart, club count, completed-match count, goals and goals per match. Match counts equal half the sum of clubs' played totals. The goal leaders use the original all-season recorded player totals; these statistics cover selected players, not complete squads.
- **Match centre:** switch between completed results and scheduled fixtures and search either participating club. Results appear newest first; scheduled fixtures appear in kickoff order. Dates use UTC, and every fixture identifies fictional or provider origin. Fixtures are labelled scheduled rather than upcoming because the dataset is historical.
- **Report studio:** all ten Phase II views remain available in their original order, with field-specific filtering, Enter-to-search, reset, sortable columns, and CSV/PDF exports of the last applied filter. Browser column sorting is presentation-only; exports retain the backend's deterministic ordering. Overview links can open a specific report.
- **Data workbench:** all eight existing CRUD entities remain available. Editing identifies the selected record, preserves single-column primary keys, and focuses the first editable field. Numeric input bounds mirror backend limits. Deletion still asks for confirmation.
- **Fixture imports:** preview, save and saved history remain separate. Save is disabled until preview succeeds and while saving; a fresh preview is required after a save attempt.
- **Accessibility:** labelled inputs, keyboard-operable sorting, visible focus, a skip link, announced feedback, and scrollable tables. Mobile navigation retains sign-out access.

The original SQL files, migration, database, authentication, role checks and persistence logic were not changed by the redesign.

### Redesign verification

From `Phase_III`, with the requirements installed:

~~~powershell
python -m unittest discover -s tests -v
node --check static/ui.js
~~~

Five integration tests pass for page rendering and escaping, guest/reader permissions, anonymous and CSRF guards, and filtered JSON/CSV/PDF responses. These tests mock SQL reads and never connect to or modify MySQL. Browser checks used an isolated fixture-response preview: desktop and 390px mobile layout, results/fixtures switching, club-search empty state, report deep links, numeric sorting, team editor selection and mobile login rendering. The dashboard produced no browser console errors during that check.

Live database CRUD, real sign-in and provider import were not re-run for this redesign because this checkout has no configured `.env`. The earlier audit above is historical, not evidence of a new live database test. Follow the demonstration procedure against your configured database before the final presentation.

The displayed group number is Group 20. The existing database remains named `group12_football_phase2`. `MYSQL_USER=group12` in .env.example is only a default, not evidence that a MySQL login exists. Use an existing authorized MySQL account. The web ADMIN account is separate from the MySQL connection account. `FOOTBALL_DATA_TOKEN` is optional for sign-in. Existing process environment variables take precedence over .env; use the intended values in the PowerShell session that launches Flask. Never rerun Phase II initialization scripts to repair a login.

## Dark frontend redesign verification

The dark redesign continues from local Git checkpoint `3e57147` on `phase3-redesign`. The checkpoint preserves the earlier Touchline implementation and Group 20 branding. No backend routes, authentication logic, SQL scripts, schema, database name, or dependency requirements were changed.

### Frontend changes

- Charcoal surfaces, emerald accents, restrained lime highlights, local stadium illustration, and local Touchline favicon across all five screens.
- Overview spotlights use the latest completed result and earliest scheduled fixture returned by the existing report APIs. They are not live-match widgets. Fictional course fixtures remain labelled; no scores or player statistics are hardcoded into production screens.
- Club comparison switches between points, goals scored, and goal difference from the selected season's standings. Negative goal differences use a muted red. Exact values remain available as text below the chart. Player bars use recorded goals and disclose partial player coverage.
- Sorting keeps the league-leader highlight tied to league position rather than row order. Report/table selectors handle rapid changes; empty and failed requests have clearer messages. Results and fixtures load independently, so one failure does not suppress the other.
- Keyboard focus, accessible sorting names, reduced-motion preferences, mobile navigation, and horizontally scrollable tables are retained.

### Checks completed for this redesign

- `python -m unittest discover -s tests -v`: **10 tests passed**, covering five page templates, escaping, Group 20 branding, guest/reader access, anonymous/CSRF guards, all ten JSON report contracts, filtered exports, missing provider token, preview-before-save, and rejection of duplicate provider IDs. SQL and provider calls are mocked in the regression suite; it does not write to MySQL.
- `node --check static/ui.js`: passed.
- Read-only integration against the configured MySQL database: **all ten reports returned JSON and generated CSV/PDF**, all eight record-list endpoints returned successfully, import history loaded, and the five templates rendered. Authentication was supplied only inside the test client; no live sign-in/session creation occurred.
- Browser review used an isolated, GET-only localhost QA server serving captured responses from those actual database reads. No synthetic replacement dataset was added to the application. Captures and QA helpers stay in ignored `work/`.
- Desktop review at 1440px and mobile review at 390px and 320px covered Overview, Login, Report Studio, Data Workbench and Fixture Imports. No page-level horizontal overflow was found; wide tables scroll within their containers. Chart switching, fixture search, report filtering/deep links, export query links, numeric sorting, all eight editor field sets, guest UI restrictions and disabled-before-preview import saving were checked. No browser console errors appeared during the reviewed dashboard interactions.

### Remaining manual verification

Live sign-in/logout, successful create/update/delete transactions, and a real provider preview/save cycle were deliberately not executed because they write sessions or database records. The configured provider token was absent during this review. Missing-token and duplicate/preview protections passed isolated tests, but that does not establish live API access. Recheck those write workflows with the group's approval before the presentation. Browser export links were checked; actual report export responses were tested separately through Flask against read-only MySQL queries.

Restart the normal Flask process if it caches templates, then hard-refresh the browser to load the latest CSS and JavaScript. Use the existing Windows setup above; do not run the Phase II initialization scripts.
