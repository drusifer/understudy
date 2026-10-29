MODEL (
  name etl.final_records,
  kind FULL,
  columns (
    record_id VARCHAR,
    transaction_date DATE,
    amount DECIMAL(18, 2),
    merchant VARCHAR,
    account VARCHAR,
    kind VARCHAR,
    transfer_partner_id VARCHAR,
    refund_original_id VARCHAR,
    refund_link_status VARCHAR,
    category VARCHAR,
    category_source VARCHAR,
    category_status VARCHAR,
    match_status VARCHAR,
    pair_method VARCHAR,
    monarch_source_row INT,
    amex_source_row INT,
    monarch_raw VARCHAR,
    amex_raw VARCHAR
  )
);

-- One record per transaction (UND-54): what it is (kind), the links to its counterpart, its
-- category, and the source rows it came from.
--   kind: transfer (a paired leg), external_transfer (a payee Jev judged one of the owner's own
--   accounts), refund (linked to its original when there is one), credit (money in that is neither),
--   invalid (no usable date or amount), purchase (everything else).
--   refund_link_status: single, chosen (Jev chose among several), unlinked (Jev's answer was not
--   usable), no_original.
--   category_status: placed, review, none (not asked about); null for kinds that carry no category.
WITH base AS (
  SELECT
    coalesce('m' || CAST(monarch_source_row AS VARCHAR), 'a' || CAST(amex_source_row AS VARCHAR)) AS record_id,
    regexp_replace(lower(trim(merchant)), '\s+', ' ', 'g') AS merchant_key,
    *
  FROM etl.purchase_pairs
),
refund_status AS (
  SELECT
    refund_id,
    any_value(link_status) AS link_status,
    max(CASE WHEN candidate_rank = 1 THEN candidate_id END) AS first_candidate
  FROM etl.refund_candidates
  GROUP BY refund_id
),
classified AS (
  SELECT
    b.*,
    t.partner_record_id,
    r.link_status AS refund_status,
    r.first_candidate,
    c.candidate_id AS chosen_candidate,
    CASE
      WHEN b.match_status = 'invalid_key' THEN 'invalid'
      WHEN t.transfer_status = 'paired' THEN 'transfer'
      WHEN t.transfer_status = 'unpaired' AND j.decision = 'external_transfer' THEN 'external_transfer'
      WHEN r.refund_id IS NOT NULL THEN 'refund'
      WHEN b.amount > 0 THEN 'credit'
      ELSE 'purchase'
    END AS kind
  FROM base AS b
  LEFT JOIN etl.transfer_pairs AS t ON t.record_id = b.record_id
  LEFT JOIN etl__dev.transfer_judgment AS j ON j.payee_key = b.merchant_key
  LEFT JOIN refund_status AS r ON r.refund_id = b.record_id
  LEFT JOIN etl__dev.refund_choice AS c ON c.refund_id = b.record_id AND c.status = 'chosen'
)
SELECT
  k.record_id,
  k.transaction_date,
  k.amount,
  k.merchant,
  k.account,
  k.kind,
  CASE WHEN k.kind = 'transfer' THEN k.partner_record_id END AS transfer_partner_id,
  CASE
    WHEN k.kind <> 'refund' THEN NULL
    WHEN k.refund_status = 'single' THEN k.first_candidate
    WHEN k.refund_status = 'needs_choice' THEN k.chosen_candidate
  END AS refund_original_id,
  CASE
    WHEN k.kind <> 'refund' THEN NULL
    WHEN k.refund_status = 'single' THEN 'single'
    WHEN k.refund_status = 'no_original' THEN 'no_original'
    WHEN k.chosen_candidate IS NOT NULL THEN 'chosen'
    ELSE 'unlinked'
  END AS refund_link_status,
  CASE WHEN k.kind IN ('purchase', 'refund', 'credit') AND m.status = 'placed' THEN m.category END AS category,
  CASE WHEN k.kind IN ('purchase', 'refund', 'credit') AND m.status = 'placed' THEN m.source END AS category_source,
  CASE WHEN k.kind IN ('purchase', 'refund', 'credit') THEN coalesce(m.status, 'none') END AS category_status,
  k.match_status,
  k.pair_method,
  k.monarch_source_row,
  k.amex_source_row,
  k.monarch_raw,
  k.amex_raw
FROM classified AS k
LEFT JOIN etl__dev.merchant_category AS m ON m.merchant_key = k.merchant_key
ORDER BY k.transaction_date NULLS LAST, k.record_id
