# Data — Meraki Service Migration & Release Readiness

> Simulated project. Meraki Industries and all data are fictional. Not affiliated with Cisco Meraki.

Fictional dataset for the project described in [`docs/01-charter.md`](../docs/01-charter.md). **Snapshot date: November 13, 2026.**

| Migration Wave | Depots | Region | Cutover | Status on Nov 13, 2026 |
|---|---|---|---|---|
| 1 | DEP-01 to DEP-10 | Southeast | Sep 25, 2026 | Live |
| 2 | DEP-11 to DEP-20 | Northeast | Oct 23, 2026 | Live |
| 3 | DEP-21 to DEP-30 | Midwest | Nov 20, 2026 (planned) | In UAT. Data shows a **NO-GO** |
| 4 | DEP-31 to DEP-40 | West | Dec 18, 2026 (planned) | In configuration |

## Files

| File | Description |
|---|---|
| `generate_data.py` | Rebuilds every CSV and `meraki.db`. Standard library only, fixed seed. Run `python data/generate_data.py` |
| `meraki.db` | SQLite database with one table per CSV. The queries are in [`/sql`](../sql) |
| `*.csv` | UTF-8, with a header row. Empty cells mean NULL. Dates use the ISO format `YYYY-MM-DD` |

## Tables

### `depots` (40 rows)
The 40 US service depots and the migration wave each belongs to.

| Column | Description |
|---|---|
| depot_id | `DEP-01` … `DEP-40` (primary key) |
| depot_name | Depot name, e.g. `Miami Service Depot` |
| region | Southeast, Northeast, Midwest or West |
| wave | Migration wave (1–4) |
| planned_cutover_date | Cutover date from the charter |
| actual_cutover_date | Date the depot went live. NULL if not yet live |
| technicians | Field technicians based at the depot |

### `legacy_tickets` (~12,000 rows)
Extract from the unsupported on-premise ticketing system covering about 3 years of history (from Oct 1, 2023). Each wave's extract stops at its load date: **Wave 1** Sep 25, **Wave 2** Oct 23, **Wave 3** Nov 6 (dress-rehearsal load), **Wave 4** Nov 13 (baseline only).

| Column | Description |
|---|---|
| ticket_id | `LT-000001` … (primary key) |
| depot_id | Owning depot |
| status | Open, In Progress, On Hold, Closed or Cancelled |
| priority | P1 (highest) to P4 |
| created_date | Date the ticket was opened |
| closed_date | Date it was closed or cancelled. NULL while it is open |
| customer_id | `CUST-xxxxx`. NULL for about 1.3% of tickets, a gap in the source data |

### `migrated_tickets` (Waves 1–3)
Records loaded into the cloud field-service platform. They contain deliberate discrepancies, so expect missing records, status mismatches, dropped dates and duplicate loads.

| Column | Description |
|---|---|
| migrated_id | `FS-0000001` … (primary key) |
| legacy_ticket_id | Source `legacy_tickets.ticket_id`. Not unique, because duplicate loads exist |
| depot_id, wave | Depot and migration wave |
| status, priority, created_date, closed_date, customer_id | Values as loaded |
| migrated_at | Load date |

**Reconciled ticket:** a migrated record exists with the same status, a `created_date`, and a `closed_date` if the ticket is Closed or Cancelled.

### `test_cases` (1,280 rows)
SIT and UAT test cases per wave.

| Column | Description |
|---|---|
| test_id | `TC-W3-UAT-001` … (primary key) |
| wave | Migration wave |
| test_type | SIT (system integration test) or UAT (user acceptance test) |
| module | Functional area, e.g. Data Migration or ERP Billing Integration |
| status | Passed, Failed, Blocked or Not Run |
| executed_date | Execution date. NULL for Blocked and Not Run |

**Pass rate** = Passed ÷ (Passed + Failed). Blocked and Not Run cases count as not executed.

### `defects` (120 rows)

| Column | Description |
|---|---|
| defect_id | `DEF-001` … (primary key) |
| wave | Migration wave |
| severity | S1 (critical) to S4 (cosmetic) |
| status | Open, In Progress, Fixed - Retest, Closed or Deferred |
| module | Functional area |
| title | Short description |
| opened_date, closed_date | `closed_date` is set only for Closed defects |

**Open defect** = any status other than Closed or Deferred.

### `readiness_criteria` (48 rows = 12 criteria × 4 waves)
Go/no-go scorecard. Criteria C01–C06 are calculated from the tables above as of `assessed_date`. Criteria C07–C12 are tracked manually (rehearsal logs, approvals, training records).

| Column | Description |
|---|---|
| wave, criterion_id | Primary key |
| criterion, category | What is measured and its area (Testing, Quality, Data, Cutover, People, Security, Support) |
| weight | Weight of the criterion. The 12 weights add up to 100 |
| comparator, threshold, unit | Target, e.g. `>= 95 %` or `<= 0 count` |
| actual_value | Measured value. NULL means not measured yet |
| score | 0–100. A met criterion scores 100. An unmet one gets partial credit: linear from a floor for `>=` targets, and minus 50 per unit over the limit for `<=` targets |
| met | Y or N |
| gate | Y for criteria that force a NO-GO on their own: C01 UAT pass rate, C03 open S1 defects, C05 reconciliation, C06 open tickets lost |
| assessed_date | Date of the assessment (the go/no-go meeting for live waves) |

**Recommendation:** GO only if every gate criterion is met **and** the weighted score is at least 90.

### `risks` (12 rows)
Risk register aligned with the charter.

| Column | Description |
|---|---|
| risk_id | `R-01` … `R-12` |
| description | Risk statement |
| probability, impact | 1 (low) to 5 (high). Risk score = probability × impact |
| owner | Stakeholder from the stakeholder register |
| response | Response strategy (Avoid, Mitigate or Accept) and the action |
| status | Open, Occurred or Closed |

## Key numbers (snapshot Nov 13, 2026)

| Wave | Reconciliation | Open tickets lost | UAT pass rate | Open S1 | Weighted score | Recommendation |
|---|---|---|---|---|---|---|
| 1 | 99.8% | 0 | 97.0% | 0 | 100.0 | GO (live) |
| 2 | 99.6% | 0 | 96.5% | 0 | 100.0 | GO (live) |
| 3 | **98.7%** | **4** | **91.1%** | **2** | **68.5** | **NO-GO** |
| 4 | not migrated | — | not started | 1 | 10.8 | NO-GO (in configuration) |
