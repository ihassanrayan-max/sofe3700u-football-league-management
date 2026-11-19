# Touchline | Group 20

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
