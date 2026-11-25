# Touchline

Football League Management and Statistics System for SOFE 3700U, Group 20.
The active dataset covers the 2023/24 Premier League matches between Arsenal,
Chelsea, Liverpool, Manchester City, Manchester United and Tottenham Hotspur.
The standings describe this six-club subset, not the full Premier League.

## Setup

Follow [the teammate setup guide](setup/fresh_database/README.md). It contains
four SQL scripts for a fresh database, Windows installation commands and local
configuration checks. Everyone should use the `main` branch.

The application runs locally with Python 3.11+, Flask and MySQL 8.0.16+.
The frontend uses HTML, CSS, vanilla JavaScript and Chart.js. PDF exports use
ReportLab. No separate frontend server is needed.

After completing setup, start the application from `Phase_III`:

```powershell
.\.venv\Scripts\python.exe -m flask --app wsgi run --host 127.0.0.1 --port 5000
```

Open http://127.0.0.1:5000/login. Each installation generates its own passwords.
Keep `.env`, passwords, backups and API keys private. Routine code updates do not
require reloading the database.

## Features

- Overview: saved match results, six-club standings, player totals and charts.
- Report Studio: ten current-season reports and the original ten Phase II views.
  Select **Phase II archive** and click **Apply filter** for the original views.
  Search runs in MySQL; CSV and PDF exports use the selected dataset and filters.
- Data Workbench: administrators manage users, competitions, seasons, clubs,
  memberships, players, matches and player statistics.
- Fixture imports: administrators preview API-Football fixtures, save them to
  MySQL and import player/team statistics for up to two fixtures per batch.
- Team directory: guests can search club names and filter by city.

Administrators can manage records and imports. Users can browse analytics and
export reports. Guests have access to the team directory only. The backend
checks permissions and validates writes, including CSRF tokens and foreign keys.

## Data and imports

Reports read saved MySQL data. External API requests happen when an administrator
fetches an import preview; valid cached responses are reused. Saving uses the
reviewed preview. Provider IDs and fixture identity checks prevent duplicate
imports and reject conflicting results.

API-Football uses league 39 and season 2023. The key stays in the backend's private
`.env`. Historical access depends on the provider account. Missing statistics
remain unknown; player totals show partial coverage rather than full-season
rankings. The original Phase II sample results are fictional and remain in the
archive. The supported legacy football-data.org mode uses the historical
2025/26 dataset; it is not the active 2023/24 scope.

## Files

- `Phase_III/`: application, dependencies, templates, assets and regression tests.
- `setup/fresh_database/`: current shared SQL snapshot and installation guide.
- Root SQL files and diagrams: original Phase II submission material.
- `Phase_III/05_phase3.sql` through `07_player_totals*.sql`: upgrades for existing
  legacy installations. They are not part of the fresh-snapshot setup.

See [the application guide](Phase_III/README.md) for endpoints, provider settings,
legacy migrations and troubleshooting. See [the cleanup audit](CLEANUP_AUDIT.md)
for the maintenance changes and verification results.

## Tests

From `Phase_III`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --test tests/player_totals_ui.test.js
```

Node.js is needed only for JavaScript tests. The suite uses mocks and isolated
in-memory data; it does not call your provider or change your MySQL database.
Live import and database checks are documented separately in the application
guide. The final report, slides, contribution matrix and team evaluation are
separate course deliverables.

Football data services: [API-Football](https://www.api-football.com/) and
[football-data.org](https://www.football-data.org/). Their data remains subject
to their terms. The original ER diagram is available as
[SVG](ER_diagram.svg) or [PNG](ER_diagram.png), with the
[relational schema](Relational_schema.svg).
