MODEL (
  name etl.reconciled_transactions,
  kind FULL,
  columns (
    match_status VARCHAR,
    transaction_date DATE,
    amount DECIMAL(18, 2),
    merchant VARCHAR,
    monarch_merchant VARCHAR,
    amex_merchant VARCHAR,
    monarch_source_row INT,
    amex_source_row INT,
    monarch_raw VARCHAR,
    amex_raw VARCHAR
  )
);

WITH monarch_counts AS (
  SELECT transaction_date, amount, count(*) AS row_count
  FROM etl.raw_monarch
  GROUP BY transaction_date, amount
),
amex_counts AS (
  SELECT transaction_date, amount, count(*) AS row_count
  FROM etl.raw_amex
  GROUP BY transaction_date, amount
),
unique_matches AS (
  SELECT mc.transaction_date, mc.amount
  FROM monarch_counts AS mc
  JOIN amex_counts AS ac USING (transaction_date, amount)
  WHERE mc.transaction_date IS NOT NULL
    AND mc.amount IS NOT NULL
    AND mc.row_count = 1
    AND ac.row_count = 1
),
matched AS (
  SELECT
    'matched' AS match_status,
    m.transaction_date,
    m.amount,
    coalesce(m.merchant, a.merchant) AS merchant,
    m.merchant AS monarch_merchant,
    a.merchant AS amex_merchant,
    m.source_row_number AS monarch_source_row,
    a.source_row_number AS amex_source_row,
    m.raw_record AS monarch_raw,
    a.raw_record AS amex_raw
  FROM unique_matches AS keys
  JOIN etl.raw_monarch AS m USING (transaction_date, amount)
  JOIN etl.raw_amex AS a USING (transaction_date, amount)
),
monarch_single AS (
  SELECT
    CASE
      WHEN m.transaction_date IS NULL OR m.amount IS NULL THEN 'invalid_key'
      WHEN coalesce(ac.row_count, 0) > 0
        AND (coalesce(mc.row_count, 0) > 1 OR coalesce(ac.row_count, 0) > 1) THEN 'ambiguous'
      ELSE 'unmatched'
    END AS match_status,
    m.transaction_date,
    m.amount,
    m.merchant,
    m.merchant AS monarch_merchant,
    CAST(NULL AS VARCHAR) AS amex_merchant,
    m.source_row_number AS monarch_source_row,
    CAST(NULL AS INT) AS amex_source_row,
    m.raw_record AS monarch_raw,
    CAST(NULL AS VARCHAR) AS amex_raw
  FROM etl.raw_monarch AS m
  LEFT JOIN monarch_counts AS mc USING (transaction_date, amount)
  LEFT JOIN amex_counts AS ac USING (transaction_date, amount)
  WHERE NOT EXISTS (
    SELECT 1 FROM unique_matches AS keys
    WHERE keys.transaction_date = m.transaction_date AND keys.amount = m.amount
  )
),
amex_single AS (
  SELECT
    CASE
      WHEN a.transaction_date IS NULL OR a.amount IS NULL THEN 'invalid_key'
      WHEN coalesce(mc.row_count, 0) > 0
        AND (coalesce(ac.row_count, 0) > 1 OR coalesce(mc.row_count, 0) > 1) THEN 'ambiguous'
      ELSE 'unmatched'
    END AS match_status,
    a.transaction_date,
    a.amount,
    a.merchant,
    CAST(NULL AS VARCHAR) AS monarch_merchant,
    a.merchant AS amex_merchant,
    CAST(NULL AS INT) AS monarch_source_row,
    a.source_row_number AS amex_source_row,
    CAST(NULL AS VARCHAR) AS monarch_raw,
    a.raw_record AS amex_raw
  FROM etl.raw_amex AS a
  LEFT JOIN amex_counts AS ac USING (transaction_date, amount)
  LEFT JOIN monarch_counts AS mc USING (transaction_date, amount)
  WHERE NOT EXISTS (
    SELECT 1 FROM unique_matches AS keys
    WHERE keys.transaction_date = a.transaction_date AND keys.amount = a.amount
  )
)
SELECT * FROM (
  SELECT * FROM matched
  UNION ALL
  SELECT * FROM monarch_single
  UNION ALL
  SELECT * FROM amex_single
) AS reconciliation_rows
ORDER BY
  CASE match_status WHEN 'matched' THEN 0 WHEN 'ambiguous' THEN 1 WHEN 'unmatched' THEN 2 ELSE 3 END,
  transaction_date NULLS LAST,
  amount NULLS LAST,
  CASE WHEN monarch_source_row IS NULL THEN 1 ELSE 0 END,
  coalesce(monarch_source_row, amex_source_row)
