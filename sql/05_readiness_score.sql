-- =============================================================================
-- 05_readiness_score.sql  |  Database: data/meraki.db (SQLite)
-- -----------------------------------------------------------------------------
-- Decision supported: the Go/No-Go recommendation for each migration wave.
--
-- Rule: GO only if every gate criterion (gate = 'Y') is met AND the weighted
-- readiness score is >= 90. Weighted score = SUM(weight * score) / SUM(weight),
-- where each criterion's score is 0-100 (100 when met, partial credit when not).
-- Gate criteria: C01 UAT pass rate, C03 open S1 defects, C05 reconciliation,
-- C06 open tickets lost.
-- Simulated project. Meraki Industries and all data are fictional.
-- =============================================================================


-- Q1. Weighted readiness score and recommendation by wave
SELECT wave,
       MAX(assessed_date)                                    AS assessed_date,
       ROUND(1.0 * SUM(weight * score) / SUM(weight), 1)     AS weighted_score,
       SUM(met = 'Y')                                        AS criteria_met,
       COUNT(*)                                              AS criteria_total,
       SUM(gate = 'Y' AND met = 'N')                         AS gates_failed,
       CASE WHEN SUM(gate = 'Y' AND met = 'N') = 0
             AND 1.0 * SUM(weight * score) / SUM(weight) >= 90
            THEN 'GO' ELSE 'NO-GO' END                       AS recommendation
FROM readiness_criteria
GROUP BY wave
ORDER BY wave;


-- Q2. Unmet criteria by wave: what must change to reach GO
SELECT wave,
       criterion_id,
       criterion,
       gate,
       comparator || ' ' ||
           CASE WHEN threshold = CAST(threshold AS INTEGER)
                THEN CAST(CAST(threshold AS INTEGER) AS TEXT) ELSE CAST(threshold AS TEXT) END
           || ' ' || unit AS target,
       CASE WHEN actual_value IS NULL THEN 'not measured'
            WHEN actual_value = CAST(actual_value AS INTEGER) THEN CAST(CAST(actual_value AS INTEGER) AS TEXT)
            ELSE CAST(actual_value AS TEXT) END AS actual,
       score,
       weight,
       weight * (100 - score) / 100.0 AS points_lost
FROM readiness_criteria
WHERE met = 'N'
ORDER BY wave, gate DESC, points_lost DESC;


-- Q3. Score by category (useful for the steering committee slide)
SELECT wave,
       category,
       SUM(weight)                                       AS weight,
       ROUND(1.0 * SUM(weight * score) / SUM(weight), 1) AS category_score
FROM readiness_criteria
GROUP BY wave, category
ORDER BY wave, category;
