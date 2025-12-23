# Implementation Plan - DataDome Scraper (Medium Scenario)

## Goal
Scrape 20,000 pages in 30 minutes (Target ~12 RPS) from `bounty-nginx.datashield.co`.

## Architecture
Using the "Production-Level" modular structure defined in `kriteria.txt`, optimized with Nginx-specific bypass strategies from `updatebacadokumentasi.txt`.

## Steps
1.  **Setup Structure**: Create directories and `requirements.txt`.
2.  **Core Components**:
    *   `config/settings.py`: Configure for 12 RPS, Burst 25, Time limit 30m.
    *   `core/client.py`: TLS client with JA4/Chrome 131 fingerprint.
    *   `core/fingerprint.py`: Basic fingerprint manager (stub).
3.  **Detection Evasion**:
    *   `detections/timing.py`: Implement burst/cooldown logic.
4.  **Utilities**:
    *   `utils/parser.py`: Regex-based parsing.
    *   `utils/metrics.py`: Progress tracking.
    *   `utils/validator.py`: Response validation (200 OK check).
5.  **Scraper Logic**:
    *   `scrapers/datadome_scraper.py`: Main loop with Nginx optimization.
6.  **Entry Point**:
    *   `main.py`: CLI entry point.

## Execution
User will need to provide the initial `datadome` cookie in `.env` or input.
