# ⚽ Touchline — Football League Management & Statistics

Touchline is a full-stack football league management and statistics application developed using Python, Flask, MySQL, HTML, CSS and JavaScript.

The application provides football statistics, league standings, SQL reports, administrative database management and external football API integration.

Developed for **SOFE 3700U — Data Management Systems, Fall 2026, Group 20**, at Ontario Tech University.

The application and database run locally.

## 📑 Table of Contents

- [Features](#-features)
- [Technologies](#-technologies)
- [Prerequisites](#-prerequisites)
- [Project Structure](#-project-structure)
- [Installation and Setup](#-installation-and-setup)
- [Roles and Access](#-roles-and-access)
- [Using the Application](#-using-the-application)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Known Limitations](#-known-limitations)
- [Contributors](#-contributors)

## 💡 Features

- User authentication and session management.
- Administrator, user and guest access roles.
- Football standings, match results and scheduled fixtures.
- Player and team statistics.
- Ten SQL-based reports.
- Search, filtering and table sorting.
- CSV and PDF report exports.
- Administrative CRUD operations through Data Workbench.
- External football data preview and import.
- Interactive charts and data visualization.
- Frontend and backend data validation.
- Error handling and role-based access restrictions.

## 📦 Technologies

| Component | Technology |
| --- | --- |
| Backend | Python, Flask |
| Database | MySQL, PyMySQL |
| Frontend | HTML, CSS, JavaScript, Jinja |
| Data Visualization | Chart.js |
| Communication | REST/JSON, Fetch API |
| External API | API-Football, football-data.org |
| Data Export | CSV, ReportLab |
| Configuration | python-dotenv |
| API Caching | SQLite |
| Testing | Python unittest, JavaScript |

## 📋 Prerequisites

Install the following before setting up the application:

- Python 3.11 or newer, including pip and the Python launcher.
- MySQL Server 8.0.16 or newer.
- MySQL Workbench.
- Git.
- Visual Studio Code.
- A web browser.

Optional:

- Node.js, for JavaScript testing.
- An API-Football account and API key, for importing real football data.

MySQL Server must be installed and running. MySQL Workbench alone is not sufficient.

## 📁 Project Structure

```text
sofe3700u-football-league-management/
│
├── Phase_III/
│   ├── static/
│   ├── templates/
│   ├── tests/
│   ├── work/
│   ├── .env.example
│   ├── 05_phase3.sql
│   ├── 06_api_football.sql
│   ├── 06_api_football_preflight.sql
│   ├── 06_api_football_verify.sql
│   ├── 07_player_totals.sql
│   ├── 07_player_totals_preflight.sql
│   ├── 07_player_totals_verify.sql
│   ├── 08_scheduled_demo.sql
│   ├── 08_scheduled_demo_preflight.sql
│   ├── 08_scheduled_demo_verify.sql
│   ├── 09_player_goal_comparison.sql
│   ├── 09_player_goal_comparison_preflight.sql
│   ├── 09_player_goal_comparison_verify.sql
│   ├── api_football.py
│   ├── app.py
│   ├── provider_store.py
│   ├── services.py
│   ├── wsgi.py
│   ├── requirements.txt
│   └── README.md
│
├── .gitignore
├── 01_create_tables.sql
├── 02_insert_data.sql
├── 03_create_views.sql
├── 04_test_queries.sql
├── ER_diagram.png
├── ER_diagram.svg
├── Relational_schema.svg
└── README.md
```

The `.env` and `.venv` files/directories are created locally during installation.

Local database exports, generated credentials and API cache files are not required repository files.

## 🚦 Installation and Setup

The following instructions are intended for Windows using Visual Studio Code PowerShell and MySQL Workbench.

Run PowerShell commands in the VS Code terminal and SQL scripts in MySQL Workbench.

### Step 1 — Clone the Repository

Open PowerShell and navigate to the directory where you want to install the project.

Run:

```powershell
git clone --branch touchline-visual-upgrade https://github.com/ihassanrayan-max/sofe3700u-football-league-management.git
```

Open the cloned repository in Visual Studio Code.

Alternatively, if the repository is already cloned, confirm that you are on the correct branch:

```powershell
git branch --show-current
```

The intended branch is:

```text
touchline-visual-upgrade
```

### Step 2 — Configure MySQL Workbench

1. Open MySQL Workbench.
2. Create or open a local MySQL connection.
3. Enter your MySQL connection username and password.
4. Test the connection.
5. Connect to the MySQL server.

The standard local configuration is:

| Setting | Value |
| --- | --- |
| Hostname | 127.0.0.1 |
| Port | 3306 |
| Username | Your MySQL username |
| Password | Your MySQL password |
| Project database | touchline_upgrade |

The original project SQL scripts may reference `group12_football_phase2`. The database used in the current local configuration is `touchline_upgrade`.

For a fresh installation, ensure that the schema creation and all applicable `USE` statements reference the same intended database. If retaining the original database name, use that name consistently in MySQL Workbench and the `.env` file instead.

Do not create two separate project databases unintentionally.

### Step 3 — Initialize the Database

In MySQL Workbench, open and execute the following SQL files individually.

Run the entire contents of each file and check for errors before proceeding to the next file.

#### Core Database Scripts

| Order | File | Purpose |
| --- | --- | --- |
| 1 | `01_create_tables.sql` | Creates the original database and core tables |
| 2 | `02_insert_data.sql` | Inserts initial sample data |
| 3 | `03_create_views.sql` | Creates the ten original SQL views |
| 4 | `04_test_queries.sql` | Verifies the original database and SQL queries |

Script 04 is a verification script and does not initialize the application database.

#### Phase III Scripts

The following files are located inside the `Phase_III` directory.

| Order | File | Purpose |
| --- | --- | --- |
| 5 | `05_phase3.sql` | Adds authentication, sessions and import tracking |
| 6 | `06_api_football_preflight.sql` | Checks readiness for API-Football migration |
| 7 | `06_api_football.sql` | Adds API-Football tables and views |
| 8 | `06_api_football_verify.sql` | Verifies API-Football migration |
| 9 | `07_player_totals_preflight.sql` | Checks player statistics views |
| 10 | `07_player_totals.sql` | Updates player statistics totals |
| 11 | `07_player_totals_verify.sql` | Verifies player statistics changes |
| 12 | `08_scheduled_demo_preflight.sql` | Checks scheduled fixture demonstration setup |
| 13 | `08_scheduled_demo.sql` | Adds isolated synthetic demonstration fixtures |
| 14 | `08_scheduled_demo_verify.sql` | Verifies scheduled fixture demonstration data |
| 15 | `09_player_goal_comparison_preflight.sql` | Checks player goal comparison views |
| 16 | `09_player_goal_comparison.sql` | Updates player goal comparison |
| 17 | `09_player_goal_comparison_verify.sql` | Verifies player goal comparison changes |

For each migration group, execute the preflight, migration and verification scripts in that order.

Review the preflight results before applying a migration. Stop if unexpected database objects, permission errors or failed checks are reported.

Migration 07 is already incorporated into the updated migration 06 for fresh installations. Its separate script is provided for updating existing installations and may be run after reviewing its preflight results.

Migration 08 installs the synthetic scheduled fixtures demonstration used in Report Studio.

After executing the scripts, refresh the Schemas panel in MySQL Workbench and confirm that the tables and views exist under the intended database.

**Important:**

- Script 01 can drop existing project tables.
- Do not rerun scripts 01 and 02 on an existing installation.
- Migration 06 is intended to be applied once.
- Back up an existing database before applying migrations.
- Do not blindly rerun a failed migration.
- Ensure that the selected database and `.env` database name match.
- SQL scripts do not need to be executed again every time the application is started.

Additional migration-specific instructions are available in [Phase_III/README.md](Phase_III/README.md).

### Step 4 — Navigate to the Application Directory

Open a PowerShell terminal in Visual Studio Code.

If the terminal is currently in the directory containing the cloned repository, run:

```powershell
cd sofe3700u-football-league-management/Phase_III
```

If the terminal is already inside the repository root, run:

```powershell
cd Phase_III
```

If the terminal path already ends in `Phase_III`, skip this step.

All remaining PowerShell commands should be executed from inside `Phase_III`.

### Step 5 — Create the Python Virtual Environment

Run:

```powershell
py -m venv .venv
```

This creates a local Python virtual environment for the application.

Skip this command if a functioning `.venv` already exists.

### Step 6 — Install Python Dependencies

Run the following commands:

```powershell
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

```powershell
& ".\.venv\Scripts\python.exe" -m pip install PyMySQL python-dotenv
```

Verify that the dependencies are available:

```powershell
& ".\.venv\Scripts\python.exe" -c "import flask, pymysql, dotenv; print('Dependencies OK')"
```

Expected output:

```text
Dependencies OK
```

The virtual environment does not need to be activated manually when its Python executable is called directly.

### Step 7 — Configure Environment Variables

Locate `.env.example` inside `Phase_III`.

Duplicate the file and rename the duplicate to `.env`.

Alternatively, run:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Open the newly created `.env` file in Visual Studio Code.

Generate a random Flask secret key:

```powershell
& ".\.venv\Scripts\python.exe" -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into the `SECRET_KEY` field.

Configure the remaining environment variables as follows:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=touchline_upgrade

SECRET_KEY=your_generated_secret_key

FOOTBALL_DATA_TOKEN=

API_FOOTBALL_KEY=
API_FOOTBALL_DAILY_LIMIT=90

TOUCHLINE_PROVIDER=api-football
```

Replace the placeholder values with your own information.

| Variable | Description |
| --- | --- |
| `MYSQL_HOST` | MySQL server hostname |
| `MYSQL_PORT` | MySQL connection port |
| `MYSQL_USER` | Your MySQL connection username |
| `MYSQL_PASSWORD` | Your MySQL connection password |
| `MYSQL_DATABASE` | Name of the project database created in Workbench |
| `SECRET_KEY` | Randomly generated Flask session secret |
| `FOOTBALL_DATA_TOKEN` | Legacy football-data.org API token |
| `API_FOOTBALL_KEY` | API-Football API key |
| `API_FOOTBALL_DAILY_LIMIT` | Local rolling API request limit |
| `TOUCHLINE_PROVIDER` | Selected external football data provider |

The MySQL username and password must match the credentials used to connect through MySQL Workbench.

Only select `api-football` after the required API-Football migration has been successfully completed.

Keep the original `.env.example` file unchanged.

Do not upload `.env`, database passwords, secret keys or API keys to GitHub.

### Step 8 — Configure the External Football API

An API key is required to retrieve new, uncached football data. It is not required to sign in or view records already stored in MySQL.

To enable real football data imports:

1. Visit https://www.api-football.com/.
2. Create an API-Football account.
3. Obtain a direct API-Sports API key.
4. Open the local `.env` file.
5. Enter the key into `API_FOOTBALL_KEY`.
6. Ensure that the selected provider is `api-football`.

```dotenv
API_FOOTBALL_KEY=your_api_key
API_FOOTBALL_DAILY_LIMIT=90
TOUCHLINE_PROVIDER=api-football
```

Ensure that your API account supports the required historical season and statistics endpoints.

The legacy football-data.org provider is also supported:

```dotenv
FOOTBALL_DATA_TOKEN=your_legacy_api_token
TOUCHLINE_PROVIDER=football-data.org
```

Legacy mode can display the original sample dataset without performing new imports.

Restart Flask after modifying `.env`.

### Step 9 — Generate Website Login Credentials

Run:

```powershell
& ".\.venv\Scripts\python.exe" -m flask --app wsgi demo-accounts
```

On a fresh installation, this command generates and displays passwords for the demo accounts.

Save the displayed credentials privately.

| Role | Email |
| --- | --- |
| ADMIN | admin.one@example.com |
| USER | reader.one@example.com |
| GUEST | guest.one@example.com |

If the credentials have already been generated, the command will not necessarily display new passwords. Use the previously saved credentials.

If the existing passwords have been lost, they can be deliberately reset using:

```powershell
& ".\.venv\Scripts\python.exe" -m flask --app wsgi reset-demo-passwords
```

This replaces all three demo account passwords. Only use it when password recovery is necessary.

Run the reset command directly in an interactive terminal.

### Step 10 — Run the Application

Start the Flask development server:

```powershell
& ".\.venv\Scripts\python.exe" -m flask --app wsgi run
```

Once the server has started, open the following URL in a web browser:

```text
http://127.0.0.1:5000/login
```

Sign in using one of the demo accounts and its generated password.

Keep the PowerShell terminal running while using the application.

To stop the application, press:

```text
Ctrl + C
```

### Subsequent Application Startup

After the initial installation, ensure MySQL Server is running and open PowerShell inside `Phase_III`.

Run:

```powershell
& ".\.venv\Scripts\python.exe" -m flask --app wsgi run
```

Open:

```text
http://127.0.0.1:5000/login
```

There is no need to recreate the database, reinstall dependencies, regenerate passwords or rerun migrations during normal startup.

## 🔐 Roles and Access

| Role | Access |
| --- | --- |
| ADMIN | Dashboard, matches, statistics, reports, exports, CRUD operations and API imports |
| USER | Dashboard, matches, statistics, reports and exports |
| GUEST | Read-only team directory with name search and city filtering |

Administrative operations are restricted through backend role validation.

Guest accounts cannot access administrative features, match statistics, charts, reports or exports.

## ⚽ Using the Application

### Overview and Match Centre

View league standings, match results, team comparisons, player statistics and scheduled fixtures.

### Report Studio

Select one of the ten available SQL reports:

1. Match Details
2. Player Goal Comparison
3. Players Who Scored
4. Match Statistics Coverage
5. Players With Goals or Assists
6. League Standings
7. Player Statistics Totals
8. Match Results
9. Scheduled Fixtures
10. Home and Away Performance

Reports support searching, filtering, sorting and CSV/PDF exports.

For Scheduled Fixtures, select the appropriate data source. Synthetic demonstration fixtures are explicitly labelled and kept separate from real football statistics.

### Data Workbench

Sign in as ADMIN to create, read, update and delete records in supported database tables.

Use disposable records when demonstrating CRUD operations to avoid modifying important project data.

### Importing Real Football Data

Sign in as ADMIN and ensure API-Football mode is configured.

1. Open Fixture Imports.
2. Select Six-club fixtures.
3. Click Fetch preview.
4. Review the returned fixture information.
5. Click Save preview to store the data in MySQL.
6. Select Next 2 fixtures: players + statistics.
7. Fetch and save the statistics preview.
8. Repeat while fixtures remain pending and the API quota permits.
9. Review the saved import history and team statistics.
10. Return to Overview or Report Studio to inspect the updated data.

Importing fixtures does not automatically import all player statistics. Player and team enrichment must be performed separately.

## 🧪 Testing

The final project report documents 71 passing Python tests and 2 passing JavaScript regression tests, alongside successful JavaScript syntax checks.

Manual testing was also performed for authentication, role management, CRUD operations, SQL reports, searching, exports, API integration and data validation.

### Python Tests

From inside `Phase_III`, run:

```powershell
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v
```

### JavaScript Regression Tests

If Node.js is installed, run:

```powershell
node --test tests/player_totals_ui.test.js tests/scheduled_fixtures_ui.test.js
```

### JavaScript Syntax Checks

```powershell
node --check static/ui.js
node --check static/guest.js
node --check static/chart.umd.min.js
```

Automated tests use mocks or isolated data and do not independently establish that a local MySQL installation or API subscription is correctly configured.

### Manual Verification

After installation, verify that:

- All three demo accounts can access their permitted interfaces.
- All ten SQL reports can be executed.
- Search, filtering and sorting work.
- CSV and PDF exports work.
- Administrators can perform CRUD operations.
- API data can be previewed and saved when a valid key is configured.
- Restricted operations are denied for unauthorized users.
- Logout terminates the current session.

## 🔧 Troubleshooting

| Problem | Solution |
| --- | --- |
| Python command not recognized | Install Python with the Windows Python launcher and reopen the terminal. |
| Cannot find Phase_III | Check the current terminal directory before using the cd command. |
| Virtual environment not found | Run `py -m venv .venv` from inside Phase_III. |
| Missing Python module | Reinstall dependencies using the virtual environment's Python executable. |
| MySQL connection refused | Ensure MySQL Server is running and check the configured host and port. |
| MySQL access denied | Verify the MySQL username, password and permissions in `.env`. |
| Unknown database | Verify that the database exists and its name matches `MYSQL_DATABASE`. |
| Missing database tables or views | Verify that the required SQL scripts were successfully executed against the correct schema. |
| Migration reports existing objects | Stop and inspect the existing migration state before proceeding. |
| Demo accounts command displays nothing | Use previously generated passwords or deliberately reset the demo passwords. |
| API authentication error | Verify the API key and selected provider. |
| API quota exceeded | Wait for the quota allowance to reset and avoid unnecessary repeated imports. |
| Player statistics missing | Import player statistics enrichment after saving fixtures. Some provider statistics may be unavailable. |
| Scheduled Fixtures report is empty | The imported season may contain only completed fixtures. Select the labelled synthetic demonstration source if required. |
| Guest account cannot view analytics | This is expected role-based behaviour. |
| Application changes are not visible | Restart Flask and hard-refresh the browser using Ctrl + Shift + R. |

If port 5000 is already occupied, run Flask on an alternative port:

```powershell
& ".\.venv\Scripts\python.exe" -m flask --app wsgi run --port 5001
```

Then open:

```text
http://127.0.0.1:5001/login
```

Additional technical troubleshooting and migration instructions can be found in [Phase_III/README.md](Phase_III/README.md).

## ⚠️ Known Limitations

- Real football data is limited to the 2023/24 Premier League matches between six selected clubs:
  - Arsenal
  - Chelsea
  - Liverpool
  - Manchester City
  - Manchester United
  - Tottenham Hotspur
- League standings represent the selected six-club subset rather than the complete Premier League.
- API request restrictions and data availability may result in incomplete player statistics.
- Unknown statistics are not treated as confirmed zero values.
- Original sample data and scheduled demonstration fixtures are fictional and are kept separate from real API-Football analytics.
- The application runs locally and is not configured for production deployment.

## 👥 Contributors

SOFE 3700U — Data Management Systems, Group 20

- Ibrahim Syed
- Mahir Patel
- Muska Ebadi
- Hassan Rayan

Ontario Tech University — Fall 2026.

## 📖 Additional Documentation

- [Detailed Installation and Migration Guide](Phase_III/README.md)
- [Entity-Relationship Diagram](ER_diagram.svg)
- [Relational Schema](Relational_schema.svg)
- [API-Football](https://www.api-football.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [Chart.js Documentation](https://www.chartjs.org/docs/latest/)