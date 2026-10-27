MODEL (
  name etl.purchase_pairs,
  kind FULL,
  columns (
    match_status VARCHAR,
    pair_method VARCHAR,
    transaction_date DATE,
    amount DECIMAL(18, 2),
    merchant VARCHAR,
    account VARCHAR,
    monarch_source_row INT,
    amex_source_row INT,
    monarch_raw VARCHAR,
    amex_raw VARCHAR
  )
);

-- One record per purchase (UND-50, ADR-0039). A Monarch row on the Amex card pairs with an
-- Amex row of the same date and the same amount, sign flipped (Amex charges are positive,
-- Monarch's negative). Inside a (date, amount) group pairing is one-to-one: rows whose
-- statement text is equal pair first, the rest pair by source row order. Amounts are kept in
-- Monarch's sign (spending negative) in the output.
WITH monarch AS (
  SELECT
    m.*,
    -m.amount AS charge_key,
    lower(trim(coalesce(m.statement, m.merchant))) AS text_key,
    (m.account = @amex_account AND m.transaction_date IS NOT NULL AND m.amount IS NOT NULL) AS eligible
  FROM etl.raw_monarch AS m
),
amex AS (
  SELECT a.*, a.amount AS charge_key, lower(trim(a.merchant)) AS text_key
  FROM etl.raw_amex AS a
  WHERE a.transaction_date IS NOT NULL AND a.amount IS NOT NULL
),
monarch_exact AS (
  SELECT
    source_row_number, transaction_date, charge_key, text_key,
    row_number() OVER (PARTITION BY transaction_date, charge_key, text_key ORDER BY source_row_number) AS rank_in_group
  FROM monarch WHERE eligible
),
amex_exact AS (
  SELECT
    source_row_number, transaction_date, charge_key, text_key,
    row_number() OVER (PARTITION BY transaction_date, charge_key, text_key ORDER BY source_row_number) AS rank_in_group
  FROM amex
),
exact_pairs AS (
  SELECT m.source_row_number AS monarch_row, a.source_row_number AS amex_row, 'exact' AS pair_method
  FROM monarch_exact AS m
  JOIN amex_exact AS a
    ON m.transaction_date = a.transaction_date
    AND m.charge_key = a.charge_key
    AND m.text_key = a.text_key
    AND m.rank_in_group = a.rank_in_group
),
monarch_left AS (
  SELECT
    source_row_number, transaction_date, charge_key,
    row_number() OVER (PARTITION BY transaction_date, charge_key ORDER BY source_row_number) AS rank_in_group
  FROM monarch
  WHERE eligible AND source_row_number NOT IN (SELECT monarch_row FROM exact_pairs)
),
amex_left AS (
  SELECT
    source_row_number, transaction_date, charge_key,
    row_number() OVER (PARTITION BY transaction_date, charge_key ORDER BY source_row_number) AS rank_in_group
  FROM amex
  WHERE source_row_number NOT IN (SELECT amex_row FROM exact_pairs)
),
order_pairs AS (
  SELECT m.source_row_number AS monarch_row, a.source_row_number AS amex_row, 'order' AS pair_method
  FROM monarch_left AS m
  JOIN amex_left AS a
    ON m.transaction_date = a.transaction_date
    AND m.charge_key = a.charge_key
    AND m.rank_in_group = a.rank_in_group
),
same_date_pairs AS (
  SELECT * FROM exact_pairs
  UNION ALL
  SELECT * FROM order_pairs
),
-- Pass 3: what is still unpaired pairs when the amount is equal and the dates are one to three
-- days apart (a charge often posts a day or two apart in the two exports), nearest date first.
-- Each Amex row takes its nearest Monarch candidate, then each Monarch row keeps its nearest
-- taker, so a row is used at most once and a tie stays unpaired.
monarch_rest AS (
  SELECT source_row_number, transaction_date, charge_key
  FROM monarch
  WHERE eligible AND source_row_number NOT IN (SELECT monarch_row FROM same_date_pairs)
),
amex_rest AS (
  SELECT source_row_number, transaction_date, charge_key
  FROM amex
  WHERE source_row_number NOT IN (SELECT amex_row FROM same_date_pairs)
),
near_candidates AS (
  SELECT
    m.source_row_number AS monarch_row,
    a.source_row_number AS amex_row,
    abs(date_diff('day', m.transaction_date, a.transaction_date)) AS day_gap
  FROM monarch_rest AS m
  JOIN amex_rest AS a
    ON m.charge_key = a.charge_key
    AND abs(date_diff('day', m.transaction_date, a.transaction_date)) BETWEEN 1 AND 3
),
amex_choice AS (
  SELECT *, row_number() OVER (PARTITION BY amex_row ORDER BY day_gap, monarch_row) AS amex_rank
  FROM near_candidates
),
monarch_choice AS (
  SELECT *, row_number() OVER (PARTITION BY monarch_row ORDER BY day_gap, amex_row) AS monarch_rank
  FROM amex_choice
  WHERE amex_rank = 1
),
near_pairs AS (
  SELECT monarch_row, amex_row, 'near_date' AS pair_method
  FROM monarch_choice
  WHERE monarch_rank = 1
),
pairs AS (
  SELECT * FROM same_date_pairs
  UNION ALL
  SELECT * FROM near_pairs
),
paired AS (
  SELECT
    'paired' AS match_status,
    p.pair_method,
    m.transaction_date,
    m.amount,
    m.merchant,
    m.account,
    m.source_row_number AS monarch_source_row,
    a.source_row_number AS amex_source_row,
    m.raw_record AS monarch_raw,
    a.raw_record AS amex_raw
  FROM pairs AS p
  JOIN etl.raw_monarch AS m ON m.source_row_number = p.monarch_row
  JOIN etl.raw_amex AS a ON a.source_row_number = p.amex_row
),
monarch_single AS (
  SELECT
    CASE WHEN m.transaction_date IS NULL OR m.amount IS NULL THEN 'invalid_key' ELSE 'monarch_only' END AS match_status,
    CAST(NULL AS VARCHAR) AS pair_method,
    m.transaction_date,
    m.amount,
    m.merchant,
    m.account,
    m.source_row_number AS monarch_source_row,
    CAST(NULL AS INT) AS amex_source_row,
    m.raw_record AS monarch_raw,
    CAST(NULL AS VARCHAR) AS amex_raw
  FROM etl.raw_monarch AS m
  WHERE m.source_row_number NOT IN (SELECT monarch_row FROM pairs)
),
amex_single AS (
  SELECT
    CASE WHEN a.transaction_date IS NULL OR a.amount IS NULL THEN 'invalid_key' ELSE 'amex_only' END AS match_status,
    CAST(NULL AS VARCHAR) AS pair_method,
    a.transaction_date,
    -a.amount AS amount,
    a.merchant,
    a.account,
    CAST(NULL AS INT) AS monarch_source_row,
    a.source_row_number AS amex_source_row,
    CAST(NULL AS VARCHAR) AS monarch_raw,
    a.raw_record AS amex_raw
  FROM etl.raw_amex AS a
  WHERE a.source_row_number NOT IN (SELECT amex_row FROM pairs)
)
SELECT * FROM (
  SELECT * FROM paired
  UNION ALL
  SELECT * FROM monarch_single
  UNION ALL
  SELECT * FROM amex_single
) AS purchase_rows
ORDER BY
  transaction_date NULLS LAST,
  amount NULLS LAST,
  coalesce(monarch_source_row, 2147483647),
  coalesce(amex_source_row, 2147483647)
