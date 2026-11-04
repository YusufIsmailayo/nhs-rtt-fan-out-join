-- =============================================================================
-- The fan-out join, in SQL
-- NHS RTT incomplete pathways, August 2026
--
-- The same two queries as notebooks 02 and 03, plus the check that catches
-- the problem before it reaches a report. I run this file in DuckDB over the
-- Parquet star that notebook 01 writes; sql/run_sql.py executes it and
-- asserts every figure equals the pandas output to the pathway.
--
-- I've written the queries themselves to run unchanged in MySQL 8: plain
-- joins, CTEs, GROUP BY / HAVING, nothing DuckDB-only. Only the preamble is
-- DuckDB-specific, and it does nothing but give the Parquet files table names.
--
-- Lines starting "-- result:" are labels sql/run_sql.py uses to pick up a
-- result set. They are ordinary comments to any other client.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Preamble (DuckDB only): the star schema as tables
--
-- Run from the repository root. In MySQL Workbench or Azure Data Studio skip
-- this block: load the five Parquet files (or CSV exports of them) as tables
-- with these same names and columns, and everything below runs as written.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW fact_incomplete_pathways AS SELECT * FROM read_parquet('data/silver/star/fact_incomplete_pathways.parquet');
CREATE OR REPLACE VIEW dim_provider             AS SELECT * FROM read_parquet('data/silver/star/dim_provider.parquet');
CREATE OR REPLACE VIEW dim_commissioner         AS SELECT * FROM read_parquet('data/silver/star/dim_commissioner.parquet');
CREATE OR REPLACE VIEW dim_treatment_function   AS SELECT * FROM read_parquet('data/silver/star/dim_treatment_function.parquet');
CREATE OR REPLACE VIEW dim_week_band            AS SELECT * FROM read_parquet('data/silver/star/dim_week_band.parquet');


-- -----------------------------------------------------------------------------
-- a. The lookup: provider -> every ICB it mainly serves
--
-- The reference table the analyst in the scenario builds: every ICB (or NHS
-- England commissioning hub) holding at least 20% of a trust's incomplete
-- pathways. Exactly as notebook 03 builds it: commissioner rolled up to its
-- parent_code, and a hub is its own parent (notebook 01 fills that in), so
-- no hub's pathways fall out of the share.
--
-- I compare in whole numbers (100 x pathways >= 20 x trust total) rather than
-- writing share >= 0.20. MySQL divides integers into a DECIMAL with only four
-- extra places by default, so a 19.996% share would round up to 0.2000 and
-- slip into the lookup. Integer arithmetic gives the same answer everywhere.
--
-- Seven NHS England hubs (Y56-Y63) have no name in the extract. GROUP BY
-- keeps their NULL-named group, so their pathways count towards each trust's
-- total. (pandas' groupby drops a NaN key by default, so notebook 03's
-- share_of_trust leaves them out. Same 621 rows either way; sql/run_sql.py
-- checks that and reports the share difference.)
--
-- This table is fine as a table. It only does damage once it's joined to the
-- fact on a key it isn't unique on.
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS ref_provider_main_icb;

CREATE TABLE ref_provider_main_icb AS
WITH share AS (
    SELECT f.provider_code,
           c.parent_code    AS icb_code,
           c.parent_name    AS icb_name,
           SUM(f.pathways)  AS pathways
    FROM fact_incomplete_pathways f
    JOIN dim_commissioner c USING (commissioner_code)
    GROUP BY f.provider_code, c.parent_code, c.parent_name
),
trust AS (
    SELECT provider_code, SUM(pathways) AS trust_pathways
    FROM share
    GROUP BY provider_code
)
SELECT s.provider_code,
       s.icb_code,
       s.icb_name,
       CAST(s.pathways AS DOUBLE) / t.trust_pathways AS share_of_trust
FROM share s
JOIN trust t USING (provider_code)
WHERE 100 * s.pathways >= 20 * t.trust_pathways;

-- result: ref_provider_main_icb
SELECT * FROM ref_provider_main_icb
ORDER BY provider_code, share_of_trust DESC;


-- -----------------------------------------------------------------------------
-- b. The correct-grain query: % over 18 weeks by treatment function
--
-- The query that passed the reconciliation gate in notebook 02. The fact
-- joins to two dimensions, both many-to-one, so every pathway is counted
-- once and the figures match NHS England's press notice Table 1 exactly.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW pct_over_18_correct AS
SELECT tf.tf_code,
       tf.tf_name,
       SUM(f.pathways)                                                      AS pathways,
       SUM(CASE WHEN w.within_18 THEN f.pathways ELSE 0 END)                AS within_18_pathways,
       100.0 * SUM(CASE WHEN w.within_18 THEN f.pathways ELSE 0 END)
             / SUM(f.pathways)                                              AS pct_within_18,
       100 - 100.0 * SUM(CASE WHEN w.within_18 THEN f.pathways ELSE 0 END)
             / SUM(f.pathways)                                              AS pct_over_18
FROM fact_incomplete_pathways f
JOIN dim_week_band          w  USING (week_band)
JOIN dim_treatment_function tf USING (tf_code)
GROUP BY tf.tf_code, tf.tf_name;

-- result: correct_grain_by_tf
SELECT * FROM pct_over_18_correct ORDER BY tf_code;


-- -----------------------------------------------------------------------------
-- c. The fan-out query: the same, plus one join
--
-- Identical to (b) apart from the last line. Someone wants to slice by ICB,
-- so the lookup goes in on provider_code, the only key the two tables share.
-- A trust with two main ICBs now has every one of its fact rows counted
-- twice, and a trust with none disappears. The query runs, no error, no
-- warning, and the percentages still look entirely plausible.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW pct_over_18_fanout AS
SELECT tf.tf_code,
       tf.tf_name,
       SUM(f.pathways)                                                      AS pathways,
       SUM(CASE WHEN w.within_18 THEN f.pathways ELSE 0 END)                AS within_18_pathways,
       100.0 * SUM(CASE WHEN w.within_18 THEN f.pathways ELSE 0 END)
             / SUM(f.pathways)                                              AS pct_within_18,
       100 - 100.0 * SUM(CASE WHEN w.within_18 THEN f.pathways ELSE 0 END)
             / SUM(f.pathways)                                              AS pct_over_18
FROM fact_incomplete_pathways f
JOIN dim_week_band          w  USING (week_band)
JOIN dim_treatment_function tf USING (tf_code)
JOIN ref_provider_main_icb     USING (provider_code)     -- the only change
GROUP BY tf.tf_code, tf.tf_name;

-- result: fan_out_rows
SELECT (SELECT COUNT(*) FROM fact_incomplete_pathways)                       AS fact_rows,
       (SELECT COUNT(*) FROM fact_incomplete_pathways
                        JOIN ref_provider_main_icb USING (provider_code))    AS rows_after_join;


-- -----------------------------------------------------------------------------
-- d. The gap, treatment function by treatment function
--
-- Fan-out minus correct, in percentage points. The rate moves only because
-- some trusts are repeated and others aren't: the result is a re-weighted
-- average, so the direction depends on who happens to be repeated.
-- -----------------------------------------------------------------------------
-- result: fan_out_by_tf
SELECT c.tf_code,
       c.tf_name,
       c.pathways                                    AS pathways_correct,
       c.pct_over_18                                 AS pct_over_18_correct,
       x.pathways                                    AS pathways_fanout,
       x.pct_over_18                                 AS pct_over_18_fanout,
       x.pct_over_18 - c.pct_over_18                 AS gap_points,
       CAST(x.pathways AS DOUBLE) / c.pathways       AS denominator_inflation
FROM pct_over_18_correct c
JOIN pct_over_18_fanout  x USING (tf_code)
ORDER BY gap_points DESC;


-- -----------------------------------------------------------------------------
-- e. The check that catches it
--
-- I run these against any lookup before I join it to a fact table. They take
-- a second and read the data, which a declared relationship never does.
--
-- 1. If the two counts differ, the key isn't unique and the join will fan out.
-- 2. Which keys repeat, and how many times.
-- 3. Which providers have no row at all, so an inner join drops them silently.
-- -----------------------------------------------------------------------------
-- result: check_key_unique
SELECT COUNT(*) AS lookup_rows, COUNT(DISTINCT provider_code) AS providers
FROM ref_provider_main_icb;

-- result: check_repeated_keys
SELECT provider_code, COUNT(*) AS lookup_rows
FROM ref_provider_main_icb
GROUP BY provider_code
HAVING COUNT(*) > 1
ORDER BY lookup_rows DESC, provider_code;

-- result: check_dropped_providers
SELECT p.provider_code, p.provider_name
FROM dim_provider p
LEFT JOIN ref_provider_main_icb r ON r.provider_code = p.provider_code
WHERE r.provider_code IS NULL
ORDER BY p.provider_code;
