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
WITH scope AS (
  SELECT coalesce(TRY_CAST(@period_start AS DATE), DATE '1900-01-01') AS start_date
),
-- The run's period: rows dated before @period_start are left out (period_scope counts them);
-- rows without a date are kept so they show up as invalid_key.
monarch_scoped AS (
  SELECT r.* FROM etl.raw_monarch AS r CROSS JOIN scope AS s
  WHERE r.transaction_date IS NULL OR r.transaction_date >= s.start_date
),
amex_scoped AS (
  SELECT r.* FROM etl.raw_amex AS r CROSS JOIN scope AS s
  WHERE r.transaction_date IS NULL OR r.transaction_date >= s.start_date
),
monarch AS (
  SELECT
    m.*,
    -m.amount AS charge_key,
    lower(trim(coalesce(m.statement, m.merchant))) AS text_key,
    (m.account = @amex_account AND m.transaction_date IS NOT NULL AND m.amount IS NOT NULL) AS eligible
  FROM monarch_scoped AS m
),
amex AS (
  SELECT a.*, a.amount AS charge_key, lower(trim(a.merchant)) AS text_key
  FROM amex_scoped AS a
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
-- Pass 3: what is still unpaired pairs when the amount is equal and the dates differ by up to
-- three business days (a charge often posts a day or two apart in the two exports, and a
-- weekend or bank holiday does not count), nearest date first.
-- Matching is one-to-one in up to five rounds: a pair is made when an Amex row and a Monarch
-- row each have the other as their nearest candidate (ties by source row), then the rows left
-- over try again, so identical fares competing for the same row all find a partner. A row is
-- used at most once; whatever is still left stays single.
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
    abs(cm.business_day_index - ca.business_day_index) AS day_gap
  FROM monarch_rest AS m
  JOIN amex_rest AS a
    ON m.charge_key = a.charge_key
    AND m.transaction_date <> a.transaction_date
  JOIN etl.business_calendar AS cm ON cm.day = m.transaction_date
  JOIN etl.business_calendar AS ca ON ca.day = a.transaction_date
  WHERE abs(cm.business_day_index - ca.business_day_index) <= 3
),
near_best1 AS (
  SELECT monarch_row, amex_row, day_gap,
    row_number() OVER (PARTITION BY amex_row ORDER BY day_gap, monarch_row) AS amex_rank,
    row_number() OVER (PARTITION BY monarch_row ORDER BY day_gap, amex_row) AS monarch_rank
  FROM near_candidates
),
near_round1 AS (
  SELECT monarch_row, amex_row FROM near_best1 WHERE amex_rank = 1 AND monarch_rank = 1
),
near_edges2 AS (
  SELECT * FROM near_candidates
  WHERE monarch_row NOT IN (SELECT monarch_row FROM near_round1) AND amex_row NOT IN (SELECT amex_row FROM near_round1)
),
near_best2 AS (
  SELECT monarch_row, amex_row, day_gap,
    row_number() OVER (PARTITION BY amex_row ORDER BY day_gap, monarch_row) AS amex_rank,
    row_number() OVER (PARTITION BY monarch_row ORDER BY day_gap, amex_row) AS monarch_rank
  FROM near_edges2
),
near_round2 AS (
  SELECT monarch_row, amex_row FROM near_best2 WHERE amex_rank = 1 AND monarch_rank = 1
),
near_edges3 AS (
  SELECT * FROM near_edges2
  WHERE monarch_row NOT IN (SELECT monarch_row FROM near_round2) AND amex_row NOT IN (SELECT amex_row FROM near_round2)
),
near_best3 AS (
  SELECT monarch_row, amex_row, day_gap,
    row_number() OVER (PARTITION BY amex_row ORDER BY day_gap, monarch_row) AS amex_rank,
    row_number() OVER (PARTITION BY monarch_row ORDER BY day_gap, amex_row) AS monarch_rank
  FROM near_edges3
),
near_round3 AS (
  SELECT monarch_row, amex_row FROM near_best3 WHERE amex_rank = 1 AND monarch_rank = 1
),
near_edges4 AS (
  SELECT * FROM near_edges3
  WHERE monarch_row NOT IN (SELECT monarch_row FROM near_round3) AND amex_row NOT IN (SELECT amex_row FROM near_round3)
),
near_best4 AS (
  SELECT monarch_row, amex_row, day_gap,
    row_number() OVER (PARTITION BY amex_row ORDER BY day_gap, monarch_row) AS amex_rank,
    row_number() OVER (PARTITION BY monarch_row ORDER BY day_gap, amex_row) AS monarch_rank
  FROM near_edges4
),
near_round4 AS (
  SELECT monarch_row, amex_row FROM near_best4 WHERE amex_rank = 1 AND monarch_rank = 1
),
near_edges5 AS (
  SELECT * FROM near_edges4
  WHERE monarch_row NOT IN (SELECT monarch_row FROM near_round4) AND amex_row NOT IN (SELECT amex_row FROM near_round4)
),
near_best5 AS (
  SELECT monarch_row, amex_row, day_gap,
    row_number() OVER (PARTITION BY amex_row ORDER BY day_gap, monarch_row) AS amex_rank,
    row_number() OVER (PARTITION BY monarch_row ORDER BY day_gap, amex_row) AS monarch_rank
  FROM near_edges5
),
near_round5 AS (
  SELECT monarch_row, amex_row FROM near_best5 WHERE amex_rank = 1 AND monarch_rank = 1
),
near_pairs AS (
  SELECT monarch_row, amex_row, 'near_date' AS pair_method FROM near_round1
  UNION ALL
  SELECT monarch_row, amex_row, 'near_date' FROM near_round2
  UNION ALL
  SELECT monarch_row, amex_row, 'near_date' FROM near_round3
  UNION ALL
  SELECT monarch_row, amex_row, 'near_date' FROM near_round4
  UNION ALL
  SELECT monarch_row, amex_row, 'near_date' FROM near_round5
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
  JOIN monarch_scoped AS m ON m.source_row_number = p.monarch_row
  JOIN amex_scoped AS a ON a.source_row_number = p.amex_row
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
  FROM monarch_scoped AS m
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
  FROM amex_scoped AS a
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
