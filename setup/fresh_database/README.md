# Touchline: fresh database setup

Use the four SQL files in **this folder only**, in order. They restore the November 24 teammate snapshot into `touchline_clean_20261124`. The existing project schema is not used or modified. Original project files remain available in their original locations.

## Why the earlier scripts conflict

The original four scripts build the Phase II sample database. Script 05 adds authentication tables. Each teammate export is a complete snapshot containing those tables, records, provider tables and views. They are alternative installation paths, not files to stack together. Running an export after the original scripts creates duplicate objects; loading both exports creates duplicate records. Rerunning the original schema reset after installing provider tables can also fail on foreign keys.

The November 24 export is the chosen baseline. It contains more recorded provider statistics than the November 20 export and includes the corrected player-totals view. Its source SHA-256 is `9481f854c8206b1b2e781491040bbcc83604134bcb4c398931b378b0076c507e`. Table definitions, insert values, synthetic flags and view definitions are retained exactly, apart from whitespace around statements and removal of export comments. New schema-selection statements and verification queries surround them.

## Before starting: install and download the project

Open PowerShell. On a new machine, install Git, Python 3.11+ (including the Windows Python launcher), MySQL Server 8.0.16+ and MySQL Workbench first. Start MySQL and confirm that Workbench connects. Each person uses their own server, credentials and local database.

Clone the application once into a folder you choose:

```powershell
git clone https://github.com/ihassanrayan-max/sofe3700u-football-league-management.git
cd sofe3700u-football-league-management
git switch main
```

If you already have a clone, open PowerShell in its root instead and update it:

```powershell
git status
git switch main
git pull --ff-only origin main
```

Commit or otherwise preserve local work before switching/updating if Git reports changes. If Git reports a conflict or divergent history, stop and resolve it; do not discard local files. The SQL files for steps 1–3 are under `setup/fresh_database` in this clone.

## 1. Prepare Workbench

1. Stop the Flask process that you plan to reconfigure. Keep the old database as a fallback.
2. Open your existing successful MySQL Workbench connection. Use MySQL 8.0.16 or newer.
3. Under **Edit > Preferences > SQL Execution**, disable **Continue on SQL script execution on errors**, if enabled. Confirm changes.
4. In a new SQL tab, execute:

```sql
SELECT VERSION(), CURRENT_USER();
SELECT SCHEMA_NAME
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'touchline_clean_20261124';
```

The second query must return zero rows. If it returns a row, stop: the name is already in use. Do not delete that schema or rerun script 01. The scripts intentionally use `CREATE DATABASE` without `IF NOT EXISTS` so an existing schema is detected.

Your MySQL account needs permission to create the new schema, tables and views and insert data. Use an authorized existing administrator for installation. The application account needs SELECT, INSERT, UPDATE and DELETE on this new schema and read access to its views and underlying tables. An account restricted to the old schema will need an administrator to grant corresponding access to the new one.

## 2. Execute the four files

Use **File > Open SQL Script** to open each file from this folder. Execute the entire file with **Ctrl+Shift+Enter**, rather than just the current statement. Review **Action Output** for errors after every file.

1. `01_create_tables.sql`: creates and selects `touchline_clean_20261124`; creates all 17 tables with foreign keys enabled.
2. `02_insert_data.sql`: loads the latest snapshot in a transaction. It contains only fresh demo identities, with no password hashes or session rows.
3. `03_create_views.sql`: creates the 25 views, including all ten original `v_*` reports, the Touchline helper views and all ten `tl_v_*` reports.
4. `04_test_queries.sql`: checks the restored counts, reads all views and checks the foreign keys.

Every file selects the new schema itself. If any file fails, stop and keep the first error message. Do not run later files or blindly rerun the failed one. If script 02 fails, run `ROLLBACK;` in that connection before investigating. MySQL table/view creation commits implicitly, so rollback does not remove already-created objects.

Do **not** also run the original SQL files, either teammate dump, or migrations 05, 06 or 07 against this schema. Their final definitions are already included. The test file here replaces the old seed-only test file for this installation.

## 3. Check the Workbench results

Refresh the Schemas panel and expand `touchline_clean_20261124`. Script 04 should show:

- 17 base tables and 25 views.
- All table-count rows have `passed = 1` before account initialization.
- 72 matches, 60 provider mappings, 478 stored provider player-stat rows and six clubs.
- Three demo users; zero login credentials and zero sessions before initialization.
- All 19 foreign-key checks show `orphan_rows = 0`.
- All view-count queries execute successfully. Exact counts are in `verification.json`.

Some real-data reports are correctly empty: `tl_v_scheduled_fixtures` has zero rows because these 30 scoped fixtures are completed; `tl_v_above_any_team_goal_total` also has zero qualifying rows. Do not fabricate records to fill those reports. The original ten Phase II reports remain present and nonempty in this snapshot.

The real-data mode covers EPL **2023/24**, matching the definitive Touchline branch. The preserved original dataset includes **2025/26**, including fictional sample records and legacy football-data.org imports. Provider flags and season filters keep them distinct. Player statistics have partial coverage; unknown is different from zero.

## 4. Use the merged Touchline application

Use `Phase_III` inside your updated clone of GitHub `main`. Do not start a separate old copy of the application. The shared snapshot is compatible with commit `34d15f8` and this setup update.

From the repository root, enter the application folder and set it up:

```powershell
cd Phase_III
if (-not (Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit that folder's private `.env` in your editor. Use the same server, port, username and password as your successful Workbench connection, with:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=your_existing_mysql_username
MYSQL_PASSWORD=your_actual_mysql_password
MYSQL_DATABASE=touchline_clean_20261124
SECRET_KEY=your_private_random_secret
TOUCHLINE_PROVIDER=api-football
API_FOOTBALL_KEY=
API_FOOTBALL_DAILY_LIMIT=90
FOOTBALL_DATA_TOKEN=
```

Replace the username, password and session-secret placeholders locally. Generate the secret with:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

No provider key is needed to display the already-loaded database records. For future API-Football imports, add your own direct API-Sports key with 2023 season access. The old football-data.org token is not an API-Football key. Keep `.env` and passwords private.

Workbench does not configure Flask environment variables. Workbench selects a MySQL connection/schema and executes SQL; the application's private `Phase_III/.env` holds its connection settings. Do not execute the dotenv settings above as SQL or edit SQL data values to change connection credentials.

Existing PowerShell environment variables override `.env`. Check what this application will actually read, without printing credentials:

```powershell
.\.venv\Scripts\python.exe -c "import app; print('Schema:', app.os.getenv('MYSQL_DATABASE')); print('Provider:', app.os.getenv('TOUCHLINE_PROVIDER'))"
.\.venv\Scripts\python.exe -c "import app; ctx=app.app.app_context(); ctx.push(); print(app.sql('SELECT DATABASE() AS connected_schema')); ctx.pop()"
```

Both schema checks must say `touchline_clean_20261124`; provider must say `api-football`. Fix the configuration before continuing if they differ. A denied connection needs correct MySQL credentials; access denied specifically for the new schema needs the appropriate account grants.

## 5. Create demo passwords and start Flask

From the same folder:

```powershell
.\.venv\Scripts\python.exe -m flask --app wsgi demo-accounts
.\.venv\Scripts\python.exe -m flask --app wsgi run --host 127.0.0.1 --port 5000
```

The first command creates salted password hashes for the three demo users and prints each generated password once. Save them privately. Passwords from the previous database do not apply. Repeating this command preserves existing passwords.

Open `http://127.0.0.1:5000/login`:

- `admin.one@example.com`: manage data, reports, exports and imports.
- `reader.one@example.com`: reports, charts, search and exports.
- `guest.one@example.com`: read-only team directory, matching Touchline permissions.

If port 5000 is occupied, stop the older Flask instance first. Refresh or sign out and sign in again after switching schemas. Restart Flask after any `.env` change. The frontend is served by this same Flask application; it needs no separate database configuration.

## 6. Demonstrate the connection

1. As admin, open the dashboard and confirm the six clubs and loaded results.
2. Open each report. Player Totals should show known subtotals with appearance-coverage columns. Check that empty real-data reports display normally.
3. Filter Match Results by a club and download CSV and PDF; compare the selected rows.
4. Open Manage data and verify records load. Use an unused test team ID to create, update and delete a disposable record.
5. Open Import and verify saved provider records display. Fetching new records is optional and requires your own API-Football key.
6. Sign in as reader and guest and verify their permissions.

## Verification record

See `verification.json` for the actual restore test status, MySQL version, source fingerprint, exact initial counts and view row counts. Tests use a separate disposable schema; they do not switch your running Flask server or modify your old database. Live API access and interactive browser appearance are separate from SQL restoration and are not claimed by this package's restore test.

If you need to return to the old setup, stop Flask, restore the previous private configuration and application folder, and restart it against the old schema. Keep the new schema available for investigation; neither installation requires deleting the other.

## Later code updates

Each teammate follows the same process on their own machine. Local database passwords, session secrets and generated demo passwords will differ, while the initial football snapshot and application code are the same.

For a routine code update, stop Flask, open PowerShell at the repository root, and run:

```powershell
git status
git switch main
git pull --ff-only origin main
cd Phase_III
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app wsgi run --host 127.0.0.1 --port 5000
```

Keep your existing `.env`, schema and passwords. Do not rerun the fresh SQL scripts for routine updates. Apply a future migration only when that update explicitly requires it. Recreating this exact initial dataset is a fresh installation into a separate empty schema; it is not a reset command for an active database.
