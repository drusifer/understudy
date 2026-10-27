MODEL (
  name etl.transfer_pairs,
  kind FULL,
  columns (
    record_id VARCHAR,
    partner_record_id VARCHAR,
    transfer_status VARCHAR,
    business_day_gap INT,
    transaction_date DATE,
    amount DECIMAL(18, 2),
    merchant VARCHAR,
    account VARCHAR
  )
);

-- Transfers between accounts (UND-51). A record is a transfer candidate when its Monarch
-- category contains "transfer" or "payment", or its Amex description contains "payment
-- received" (Amex's wording for a payment made to the card; a merchant whose name only
-- contains "payment" is not a transfer).
-- Two candidates in different accounts with opposite amounts, at most 3 days apart, are
-- linked to each other; both stay in the data and both are flagged. "At most 3 days" means
-- 3 business days (etl.business_calendar: Monday to Friday, not a US federal holiday), so a
-- Friday payment that lands on Monday, or on the Tuesday after a Monday holiday, is 1.
-- Matching is
-- one-to-one: in up to three rounds each candidate takes its nearest partner and a pair is
-- made when two candidates choose each other (ties by record id), so two same-amount
-- payments in one week each get their own partner. Candidates left over are 'unpaired'.
WITH records AS (
  SELECT
    coalesce('m' || CAST(monarch_source_row AS VARCHAR), 'a' || CAST(amex_source_row AS VARCHAR)) AS record_id,
    transaction_date,
    amount,
    merchant,
    account,
    lower(coalesce(json_extract_string(monarch_raw, '$."Category"'), '')) AS category,
    lower(coalesce(json_extract_string(amex_raw, '$."Description"'), '')) AS amex_description
  FROM etl.purchase_pairs
  WHERE match_status IN ('paired', 'monarch_only', 'amex_only')
    AND transaction_date IS NOT NULL
    AND amount IS NOT NULL
),
candidates AS (
  SELECT * FROM records
  WHERE category LIKE '%transfer%' OR category LIKE '%payment%' OR amex_description LIKE '%payment received%'
),
edges AS (
  SELECT
    a.record_id AS id,
    b.record_id AS partner,
    abs(ca.business_day_index - cb.business_day_index) AS gap
  FROM candidates AS a
  JOIN candidates AS b
    ON a.record_id <> b.record_id
    AND a.account <> b.account
    AND a.amount = -b.amount
  JOIN etl.business_calendar AS ca ON ca.day = a.transaction_date
  JOIN etl.business_calendar AS cb ON cb.day = b.transaction_date
  WHERE abs(ca.business_day_index - cb.business_day_index) <= 3
),
best1 AS (
  SELECT id, partner, gap, row_number() OVER (PARTITION BY id ORDER BY gap, partner) AS rk FROM edges
),
round1 AS (
  SELECT x.id, x.partner, x.gap
  FROM best1 AS x
  JOIN best1 AS y ON x.partner = y.id AND y.partner = x.id AND y.rk = 1
  WHERE x.rk = 1
),
edges2 AS (
  SELECT * FROM edges
  WHERE id NOT IN (SELECT id FROM round1) AND partner NOT IN (SELECT id FROM round1)
),
best2 AS (
  SELECT id, partner, gap, row_number() OVER (PARTITION BY id ORDER BY gap, partner) AS rk FROM edges2
),
round2 AS (
  SELECT x.id, x.partner, x.gap
  FROM best2 AS x
  JOIN best2 AS y ON x.partner = y.id AND y.partner = x.id AND y.rk = 1
  WHERE x.rk = 1
),
edges3 AS (
  SELECT * FROM edges2
  WHERE id NOT IN (SELECT id FROM round2) AND partner NOT IN (SELECT id FROM round2)
),
best3 AS (
  SELECT id, partner, gap, row_number() OVER (PARTITION BY id ORDER BY gap, partner) AS rk FROM edges3
),
round3 AS (
  SELECT x.id, x.partner, x.gap
  FROM best3 AS x
  JOIN best3 AS y ON x.partner = y.id AND y.partner = x.id AND y.rk = 1
  WHERE x.rk = 1
),
links AS (
  SELECT * FROM round1
  UNION ALL
  SELECT * FROM round2
  UNION ALL
  SELECT * FROM round3
)
SELECT
  c.record_id,
  l.partner AS partner_record_id,
  CASE WHEN l.partner IS NULL THEN 'unpaired' ELSE 'paired' END AS transfer_status,
  CAST(l.gap AS INT) AS business_day_gap,
  c.transaction_date,
  c.amount,
  c.merchant,
  c.account
FROM candidates AS c
LEFT JOIN links AS l ON l.id = c.record_id
ORDER BY c.record_id
