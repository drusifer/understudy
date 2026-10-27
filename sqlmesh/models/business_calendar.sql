MODEL (
  name etl.business_calendar,
  kind FULL,
  columns (
    day DATE,
    is_business_day BOOLEAN,
    business_day_index INT
  )
);

-- Every day from @calendar_start to @calendar_end with whether banks are open (Monday to
-- Friday, not a US federal holiday) and a running count of business days. A weekend or
-- holiday shares the index of the business day before it, so the gap between two dates is
-- abs(index difference) in business days: Friday to Monday is 1, Friday to the Tuesday after
-- a Monday holiday is 1, and two days of one weekend are 0.
WITH days AS (
  SELECT CAST(d AS DATE) AS day
  FROM generate_series(CAST(@calendar_start AS DATE), CAST(@calendar_end AS DATE), INTERVAL 1 DAY) AS series(d)
),
flagged AS (
  SELECT
    day,
    (dayofweek(day) BETWEEN 1 AND 5 AND day NOT IN (SELECT holiday_date FROM etl.us_federal_holidays)) AS is_business_day
  FROM days
)
SELECT
  day,
  is_business_day,
  CAST(sum(CASE WHEN is_business_day THEN 1 ELSE 0 END) OVER (ORDER BY day) AS INT) AS business_day_index
FROM flagged
ORDER BY day
