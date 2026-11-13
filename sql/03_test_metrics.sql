-- =============================================================================
-- 03_test_metrics.sql  |  Database: data/meraki.db (SQLite)
-- -----------------------------------------------------------------------------
-- Decision supported: Go/No-Go gate C01 "UAT pass rate >= 95%" (and C02 for
-- SIT), and where to focus re-testing.
--
-- Definitions:
--   executed  = Passed + Failed (Blocked and Not Run were not executed)
--   pass rate = Passed / executed
--   execution = executed / total test cases
-- Simulated project. Meraki Industries and all data are fictional.
-- =============================================================================


-- Q1. Pass rate and execution progress by wave and test type
SELECT wave,
       test_type,
       COUNT(*)                                              AS total_cases,
       SUM(status = 'Passed')                                AS passed,
       SUM(status = 'Failed')                                AS failed,
       SUM(status = 'Blocked')                               AS blocked,
       SUM(status = 'Not Run')                               AS not_run,
       ROUND(100.0 * SUM(status IN ('Passed', 'Failed')) / COUNT(*), 1) AS execution_pct,
       ROUND(100.0 * SUM(status = 'Passed')
             / NULLIF(SUM(status IN ('Passed', 'Failed')), 0), 1)       AS pass_rate_pct,
       CASE
           WHEN SUM(status IN ('Passed', 'Failed')) = 0 THEN 'NOT STARTED'
           WHEN 100.0 * SUM(status = 'Passed') / SUM(status IN ('Passed', 'Failed')) >= 95 THEN 'MET'
           ELSE 'NOT MET'
       END                                                   AS gate_95
FROM test_cases
GROUP BY wave, test_type
ORDER BY wave, test_type;


-- Q2. Failed and blocked UAT cases by module for waves still in progress
--     Decision: which modules need fixes and re-test before the next go/no-go.
SELECT t.wave,
       t.module,
       SUM(t.status = 'Failed')  AS failed,
       SUM(t.status = 'Blocked') AS blocked,
       SUM(t.status = 'Not Run') AS not_run
FROM test_cases t
WHERE t.test_type = 'UAT'
  AND t.wave IN (SELECT wave FROM depots WHERE actual_cutover_date IS NULL)
GROUP BY t.wave, t.module
HAVING SUM(t.status IN ('Failed', 'Blocked', 'Not Run')) > 0
ORDER BY t.wave, failed DESC, blocked DESC;
