-- =============================================================================
-- 04_defect_aging.sql  |  Database: data/meraki.db (SQLite)
-- -----------------------------------------------------------------------------
-- Decision supported: Go/No-Go gates C03 "0 open S1 defects" and C04
-- "<= 2 open S2 defects", and escalation of defects that are ageing.
--
-- Open defect = status not in ('Closed', 'Deferred').
-- Age in days is measured against the snapshot date 2026-11-13 (change the
-- as_of value in each query to re-run for another date).
-- Simulated project. Meraki Industries and all data are fictional.
-- =============================================================================


-- Q1. Open defects by wave and severity, with age statistics
WITH params AS (SELECT '2026-11-13' AS as_of),
open_defects AS (
    SELECT d.*, CAST(julianday(p.as_of) - julianday(d.opened_date) AS INTEGER) AS age_days
    FROM defects d CROSS JOIN params p
    WHERE d.status NOT IN ('Closed', 'Deferred')
)
SELECT wave,
       severity,
       COUNT(*)                AS open_defects,
       ROUND(AVG(age_days), 1) AS avg_age_days,
       MAX(age_days)           AS max_age_days
FROM open_defects
GROUP BY wave, severity
ORDER BY wave, severity;


-- Q2. Open defects by age bucket (all waves)
--     Decision: which defects to escalate with the vendor (anything > 14 days).
WITH params AS (SELECT '2026-11-13' AS as_of),
open_defects AS (
    SELECT d.severity, CAST(julianday(p.as_of) - julianday(d.opened_date) AS INTEGER) AS age_days
    FROM defects d CROSS JOIN params p
    WHERE d.status NOT IN ('Closed', 'Deferred')
)
SELECT severity,
       SUM(age_days <= 7)                   AS age_0_7,
       SUM(age_days BETWEEN 8 AND 14)       AS age_8_14,
       SUM(age_days BETWEEN 15 AND 30)      AS age_15_30,
       SUM(age_days > 30)                   AS age_over_30,
       COUNT(*)                             AS total_open
FROM open_defects
GROUP BY severity
ORDER BY severity;


-- Q3. Open S1/S2 defects in detail (blockers for the next go/no-go)
WITH params AS (SELECT '2026-11-13' AS as_of)
SELECT d.wave, d.defect_id, d.severity, d.status, d.module, d.title, d.opened_date,
       CAST(julianday(p.as_of) - julianday(d.opened_date) AS INTEGER) AS age_days
FROM defects d CROSS JOIN params p
WHERE d.status NOT IN ('Closed', 'Deferred')
  AND d.severity IN ('S1', 'S2')
ORDER BY d.wave, d.severity, age_days DESC;


-- Q4. Mean time to close by severity (closed defects)
--     Decision: realistic fix lead time when planning the Wave 3 re-test.
SELECT severity,
       COUNT(*)                                                      AS closed_defects,
       ROUND(AVG(julianday(closed_date) - julianday(opened_date)), 1) AS avg_days_to_close
FROM defects
WHERE status = 'Closed'
GROUP BY severity
ORDER BY severity;
