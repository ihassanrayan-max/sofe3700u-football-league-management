# Football League Management and Statistics System

SOFE 3700U Group 20 course project. This repository contains a MySQL database design and a local Flask web application for a six-club teaching subset of the 2025/26 English Premier League.

The Phase II seed fixtures, scores, and player statistics are **fictional**. The Phase III administrator import uses football-data.org API v4 and marks imported matches separately. No API token, database password, demo password, or database dump is included.

## Contents

- `01_create_tables.sql` through `04_test_queries.sql`: Phase II schema, sample data, ten views, and checks.
- `ER_diagram.svg`, `ER_diagram.png`, and `Relational_schema.svg`: database diagrams.
- `Phase_III/`: Flask application, additive migration, frontend, dependencies, and [Windows setup instructions](Phase_III/README.md).

## Run locally

Read [Phase_III/README.md](Phase_III/README.md) before running SQL. In particular, `01_create_tables.sql` resets the Phase II demo schema if rerun; do not run it against an existing project database. Configure private values in `Phase_III/.env`, copied from `.env.example`. Never commit that file.

This project is intended for a local course demonstration; this repository does not host the application or its MySQL database.
