MODEL (
  name etl.period_scope,
  kind FULL,
  columns (
    source VARCHAR,
    rows_read BIGINT,
    rows_in_period BIGINT,
    rows_before_period BIGINT,
    rows_without_date BIGINT
  )
);

-- What each export holds and how much of it the run's period leaves out (the run summary says so).
-- The period starts at @period_start; an empty value means no limit.
WITH scope AS (
  SELECT coalesce(TRY_CAST(@period_start AS DATE), DATE '1900-01-01') AS start_date
),
rows_all AS (
  SELECT 'monarch' AS source, transaction_date FROM etl.raw_monarch
  UNION ALL
  SELECT 'amex' AS source, transaction_date FROM etl.raw_amex
)
SELECT
  r.source,
  count(*) AS rows_read,
  count(*) FILTER (WHERE r.transaction_date >= s.start_date) AS rows_in_period,
  count(*) FILTER (WHERE r.transaction_date < s.start_date) AS rows_before_period,
  count(*) FILTER (WHERE r.transaction_date IS NULL) AS rows_without_date
FROM rows_all AS r
CROSS JOIN scope AS s
GROUP BY r.source
ORDER BY r.source
