-- =============================================================================
-- 01_reconciliation.sql  |  Database: data/meraki.db (SQLite)
-- -----------------------------------------------------------------------------
-- Decision supported: Go/No-Go gates C05 "Ticket reconciliation >= 99.5%" and
-- C06 "0 open tickets lost in migration". Tells the steering committee whether
-- every legacy ticket in a wave's scope arrived in the new platform intact.
--
-- A legacy ticket is RECONCILED when at least one migrated record exists for it
-- with the same status, a created_date, and a closed_date if it is Closed or
-- Cancelled. Waves without a migration load (Wave 4) are excluded.
-- Simulated project. Meraki Industries and all data are fictional.
-- =============================================================================


-- Q1. Legacy vs migrated record counts by wave
--     Decision: is the load complete, and are there duplicate loads to clean up?
WITH legacy AS (
    SELECT d.wave, COUNT(*) AS legacy_tickets
    FROM legacy_tickets t
    JOIN depots d ON d.depot_id = t.depot_id
    GROUP BY d.wave
),
migrated AS (
    SELECT wave,
           COUNT(*)                         AS migrated_rows,
           COUNT(DISTINCT legacy_ticket_id) AS migrated_tickets
    FROM migrated_tickets
    GROUP BY wave
)
SELECT l.wave,
       l.legacy_tickets,
       COALESCE(m.migrated_rows, 0)                                  AS migrated_rows,
       COALESCE(m.migrated_tickets, 0)                               AS migrated_distinct_tickets,
       COALESCE(m.migrated_rows, 0) - COALESCE(m.migrated_tickets, 0) AS duplicate_rows
FROM legacy l
LEFT JOIN migrated m ON m.wave = l.wave
ORDER BY l.wave;


-- Q2. Missing tickets by wave (in legacy, absent from the migration load)
--     Decision: any missing OPEN ticket breaks the "0 open tickets lost" gate.
SELECT d.wave,
       COUNT(*) AS missing_tickets,
       SUM(CASE WHEN t.status IN ('Open', 'In Progress', 'On Hold') THEN 1 ELSE 0 END) AS missing_open_tickets,
       SUM(CASE WHEN t.status IN ('Closed', 'Cancelled')            THEN 1 ELSE 0 END) AS missing_closed_tickets
FROM legacy_tickets t
JOIN depots d ON d.depot_id = t.depot_id
WHERE d.wave IN (SELECT DISTINCT wave FROM migrated_tickets)
  AND NOT EXISTS (SELECT 1 FROM migrated_tickets m WHERE m.legacy_ticket_id = t.ticket_id)
GROUP BY d.wave
ORDER BY d.wave;


-- Q3. Missing OPEN tickets, listed for remediation by the service desk
--     Decision: which customer tickets must be re-loaded before cutover.
SELECT d.wave, t.ticket_id, t.depot_id, d.depot_name, t.status, t.priority, t.created_date, t.customer_id
FROM legacy_tickets t
JOIN depots d ON d.depot_id = t.depot_id
WHERE d.wave IN (SELECT DISTINCT wave FROM migrated_tickets)
  AND t.status IN ('Open', 'In Progress', 'On Hold')
  AND NOT EXISTS (SELECT 1 FROM migrated_tickets m WHERE m.legacy_ticket_id = t.ticket_id)
ORDER BY d.wave, t.priority, t.created_date;


-- Q4. Reconciliation rate by wave vs the 99.5% threshold
--     Decision: the reconciliation gate (C05) for the go/no-go meeting.
WITH scope AS (
    SELECT t.ticket_id, t.status, d.wave
    FROM legacy_tickets t
    JOIN depots d ON d.depot_id = t.depot_id
    WHERE d.wave IN (SELECT DISTINCT wave FROM migrated_tickets)
),
checked AS (
    SELECT s.wave,
           EXISTS (SELECT 1 FROM migrated_tickets m
                   WHERE m.legacy_ticket_id = s.ticket_id) AS is_migrated,
           EXISTS (SELECT 1 FROM migrated_tickets m
                   WHERE m.legacy_ticket_id = s.ticket_id
                     AND m.status = s.status
                     AND m.created_date IS NOT NULL
                     AND (m.status NOT IN ('Closed', 'Cancelled') OR m.closed_date IS NOT NULL)) AS is_reconciled
    FROM scope s
)
SELECT wave,
       COUNT(*)                                        AS legacy_tickets,
       SUM(is_migrated)                                AS migrated,
       SUM(is_reconciled)                              AS reconciled,
       COUNT(*) - SUM(is_reconciled)                   AS discrepancies,
       ROUND(100.0 * SUM(is_reconciled) / COUNT(*), 1) AS reconciliation_pct,
       CASE WHEN 100.0 * SUM(is_reconciled) / COUNT(*) >= 99.5 THEN 'MET' ELSE 'NOT MET' END AS gate_99_5
FROM checked
GROUP BY wave
ORDER BY wave;
