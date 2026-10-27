MODEL (
  name etl.refund_candidates,
  kind FULL,
  columns (
    refund_id VARCHAR,
    refund_date DATE,
    refund_amount DECIMAL(18, 2),
    merchant VARCHAR,
    refund_account VARCHAR,
    candidate_id VARCHAR,
    candidate_date DATE,
    candidate_amount DECIMAL(18, 2),
    candidate_rank INT,
    candidate_count INT,
    link_status VARCHAR
  )
);

-- Refunds and their possible originals (UND-52). A refund is a credit (positive in Monarch's
-- sign) that is not a transfer leg and not income. Its possible originals are earlier or
-- same-day charges from the same merchant key (trimmed, case ignored) whose amount is at
-- least the refund's, most recent first. Only the five most recent are listed, but
-- candidate_count is the full count. link_status: no_original (none), single (linked without
-- asking), needs_choice (Jev chooses among the listed candidates).
WITH records AS (
  SELECT
    coalesce('m' || CAST(monarch_source_row AS VARCHAR), 'a' || CAST(amex_source_row AS VARCHAR)) AS record_id,
    transaction_date,
    amount,
    trim(merchant) AS merchant,
    lower(trim(merchant)) AS merchant_key,
    account,
    lower(coalesce(json_extract_string(monarch_raw, '$."Category"'), '')) AS category
  FROM etl.purchase_pairs
  WHERE match_status IN ('paired', 'monarch_only', 'amex_only')
    AND transaction_date IS NOT NULL
    AND amount IS NOT NULL
),
plain AS (
  SELECT * FROM records WHERE record_id NOT IN (SELECT record_id FROM etl.transfer_pairs)
),
refunds AS (
  SELECT * FROM plain
  WHERE amount > 0
    AND category NOT LIKE '%income%'
    AND category NOT LIKE '%paycheck%'
    AND category NOT LIKE '%interest%'
    AND category NOT LIKE '%payroll%'
),
charges AS (
  SELECT * FROM plain WHERE amount < 0
),
eligible AS (
  SELECT
    r.record_id AS refund_id,
    c.record_id AS candidate_id,
    c.transaction_date AS candidate_date,
    c.amount AS candidate_amount,
    row_number() OVER (PARTITION BY r.record_id ORDER BY c.transaction_date DESC, c.record_id DESC) AS candidate_rank,
    count(*) OVER (PARTITION BY r.record_id) AS candidate_count
  FROM refunds AS r
  JOIN charges AS c
    ON c.merchant_key = r.merchant_key
    AND c.transaction_date <= r.transaction_date
    AND -c.amount >= r.amount
)
SELECT
  r.record_id AS refund_id,
  r.transaction_date AS refund_date,
  r.amount AS refund_amount,
  r.merchant,
  r.account AS refund_account,
  e.candidate_id,
  e.candidate_date,
  e.candidate_amount,
  CAST(e.candidate_rank AS INT) AS candidate_rank,
  CAST(coalesce(e.candidate_count, 0) AS INT) AS candidate_count,
  CASE
    WHEN e.candidate_id IS NULL THEN 'no_original'
    WHEN e.candidate_count = 1 THEN 'single'
    ELSE 'needs_choice'
  END AS link_status
FROM refunds AS r
LEFT JOIN eligible AS e ON e.refund_id = r.record_id AND e.candidate_rank <= 5
ORDER BY r.transaction_date, r.record_id, e.candidate_rank
