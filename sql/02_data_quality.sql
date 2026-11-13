-- =============================================================================
-- 02_data_quality.sql  |  Database: data/meraki.db (SQLite)
-- -----------------------------------------------------------------------------
-- Decision supported: what the data team must fix before the next migration
-- load. Breaks the reconciliation gap (01_reconciliation.sql) into root causes:
-- null fields, duplicate loads and status mapping errors, plus gaps that
-- already exist in the legacy source.
-- Simulated project. Meraki Industries and all data are fictional.
-- =============================================================================


-- Q1. Null critical fields in the migrated data, by wave
--     Decision: which load rules (date mapping) need a fix.
SELECT wave,
       COUNT(*)                                                         AS migrated_rows,
       SUM(CASE WHEN created_date IS NULL THEN 1 ELSE 0 END)            AS null_created_date,
       SUM(CASE WHEN status IN ('Closed', 'Cancelled')
                 AND closed_date IS NULL THEN 1 ELSE 0 END)             AS closed_without_closed_date,
       SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END)             AS null_customer_id
FROM migrated_tickets
GROUP BY wave
ORDER BY wave;


-- Q2. Duplicate loads: legacy tickets loaded more than once
--     Decision: duplicates must be removed before go-live to avoid double billing.
SELECT wave, legacy_ticket_id, COUNT(*) AS copies, GROUP_CONCAT(migrated_id, ', ') AS migrated_ids
FROM migrated_tickets
GROUP BY wave, legacy_ticket_id
HAVING COUNT(*) > 1
ORDER BY wave, legacy_ticket_id;


-- Q3. Duplicate summary by wave
SELECT wave, COUNT(*) AS duplicated_tickets, SUM(copies - 1) AS extra_rows
FROM (SELECT wave, legacy_ticket_id, COUNT(*) AS copies
      FROM migrated_tickets
      GROUP BY wave, legacy_ticket_id
      HAVING COUNT(*) > 1)
GROUP BY wave
ORDER BY wave;


-- Q4. Status mismatches (legacy status -> migrated status), by wave
--     Decision: which status mapping rules are wrong in the migration tool.
SELECT m.wave,
       t.status  AS legacy_status,
       m.status  AS migrated_status,
       COUNT(DISTINCT t.ticket_id) AS tickets
FROM migrated_tickets m
JOIN legacy_tickets t ON t.ticket_id = m.legacy_ticket_id
WHERE m.status <> t.status
GROUP BY m.wave, t.status, m.status
ORDER BY m.wave, tickets DESC;


-- Q5. Data quality at the source: legacy tickets without a customer
--     Decision: source cleansing owned by depot data owners (not a load error).
SELECT d.wave,
       COUNT(*)                                              AS legacy_tickets,
       SUM(CASE WHEN t.customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
       ROUND(100.0 * SUM(CASE WHEN t.customer_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS null_customer_pct
FROM legacy_tickets t
JOIN depots d ON d.depot_id = t.depot_id
GROUP BY d.wave
ORDER BY d.wave;
