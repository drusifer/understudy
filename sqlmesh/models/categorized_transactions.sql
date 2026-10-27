MODEL (
  name etl.categorized_transactions,
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
    amex_raw VARCHAR,
    category VARCHAR,
    subcategory VARCHAR,
    classification_status VARCHAR,
    classification_confidence DOUBLE,
    taxonomy_version VARCHAR,
    decision_model VARCHAR,
    review_required BOOLEAN
  )
);

SELECT
  transactions.match_status,
  transactions.transaction_date,
  transactions.amount,
  transactions.merchant,
  transactions.monarch_merchant,
  transactions.amex_merchant,
  transactions.monarch_source_row,
  transactions.amex_source_row,
  transactions.monarch_raw,
  transactions.amex_raw,
  coalesce(category_map.category, 'Misc') AS category,
  coalesce(category_map.subcategory, 'Other or not yet classified') AS subcategory,
  coalesce(
    category_map.classification_status,
    CASE WHEN nullif(trim(transactions.merchant), '') IS NULL THEN 'missing_merchant' ELSE 'unclassified' END
  ) AS classification_status,
  category_map.confidence AS classification_confidence,
  category_map.taxonomy_version,
  category_map.decision_model,
  coalesce(category_map.review_required, true)
    OR transactions.match_status IN ('ambiguous', 'invalid_key') AS review_required
FROM etl.reconciled_transactions AS transactions
LEFT JOIN etl__dev.category_map AS category_map
  ON lower(trim(transactions.merchant)) = category_map.merchant_key
