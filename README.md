# Football League Management and Statistics System

SOFE 3700U Group 20 course project. This repository contains a MySQL database design and a local Flask web application for six project clubs. An API-Football EPL 2023/24 integration runs alongside the preserved football-data.org 2025/26 dataset.

The Phase II seed fixtures, scores, and player statistics are **fictional**. The Phase III administrator import supports API-Football 2023/24 after an approved additive migration and explicit provider switch. Until then, football-data.org API v4 remains the default. New-mode reports exclude fictional and other-season records before aggregation; historical records and all ten original SQL views remain intact. No API token, database password, demo password, or database dump is included.

## Contents

- `01_create_tables.sql` through `04_test_queries.sql`: Phase II schema, sample data, ten views, and checks.
- `ER_diagram.svg`, `ER_diagram.png`, and `Relational_schema.svg`: database diagrams.
- `Phase_III/`: Flask application, additive migration, frontend, dependencies, and [Windows setup instructions](Phase_III/README.md).

## Provider switch

Read the cutover instructions at the top of [Phase_III/README.md](Phase_III/README.md). The project owner has confirmed successful migration (17 tables, 25 views), import of 30 real 2023/24 fixtures, and live player-statistics/goal-leader checks. All 30 legacy imports remain preserved. Enrichment is temporarily paused by the local quota. Do not rerun `06_api_football.sql` on the migrated installation. Fresh installations must review and apply it before enabling API-Football mode; no database reset is required.

## Run locally

Read [Phase_III/README.md](Phase_III/README.md) before running SQL. In particular, `01_create_tables.sql` resets the Phase II demo schema if rerun; do not run it against an existing project database. Configure private values in `Phase_III/.env`, copied from `.env.example`. Never commit that file.

This project is intended for a local course demonstration; this repository does not host the application or its MySQL database.
