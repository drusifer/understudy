MODEL (
  name etl.merchant_candidates,
  kind FULL,
  columns (
    merchant_key VARCHAR,
    merchant VARCHAR,
    records BIGINT,
    example_amounts DOUBLE[],
    statements VARCHAR[]
  )
);

-- The distinct merchants to place in a category (UND-53, UND-55), one row per merchant key
-- (trimmed, lower case, spaces collapsed), with how many records it covers, up to three example
-- amounts and up to three statement texts (Monarch's original statement, Amex's description).
-- Paired transfer legs and unpaired candidates whose payee Jev judged an external transfer are not
-- spending (same rule as refund_candidates), so they are not placed.
WITH records AS (
  SELECT
    coalesce('m' || CAST(monarch_source_row AS VARCHAR), 'a' || CAST(amex_source_row AS VARCHAR)) AS record_id,
    transaction_date,
    amount,
    trim(merchant) AS merchant,
    regexp_replace(lower(trim(merchant)), '\s+', ' ', 'g') AS merchant_key,
    trim(json_extract_string(monarch_raw, '$."Original Statement"')) AS monarch_statement,
    trim(json_extract_string(amex_raw, '$."Description"')) AS amex_statement
  FROM etl.purchase_pairs
  WHERE match_status IN ('paired', 'monarch_only', 'amex_only')
    AND merchant IS NOT NULL
    AND trim(merchant) <> ''
),
spend AS (
  SELECT * FROM records
  WHERE record_id NOT IN (SELECT record_id FROM etl.transfer_pairs WHERE transfer_status = 'paired')
    AND NOT (
      record_id IN (SELECT record_id FROM etl.transfer_pairs WHERE transfer_status = 'unpaired')
      AND merchant_key IN (SELECT payee_key FROM etl__dev.transfer_judgment WHERE decision = 'external_transfer')
    )
),
texts AS (
  SELECT merchant_key, monarch_statement AS text FROM spend
  UNION ALL
  SELECT merchant_key, amex_statement AS text FROM spend
),
statement_lists AS (
  SELECT
    merchant_key,
    array_slice(list_sort(list_distinct(list(text) FILTER (WHERE text IS NOT NULL AND text <> ''))), 1, 3) AS statements
  FROM texts
  GROUP BY merchant_key
),
summary AS (
  SELECT
    merchant_key,
    first(merchant ORDER BY transaction_date, record_id) AS merchant,
    count(*) AS records,
    array_slice(list(CAST(amount AS DOUBLE) ORDER BY transaction_date, record_id), 1, 3) AS example_amounts
  FROM spend
  GROUP BY merchant_key
)
SELECT
  s.merchant_key,
  s.merchant,
  s.records,
  s.example_amounts,
  coalesce(l.statements, CAST([] AS VARCHAR[])) AS statements
FROM summary AS s
LEFT JOIN statement_lists AS l USING (merchant_key)
ORDER BY s.merchant_key
