MODEL (
  name etl.offered_categories,
  kind FULL,
  columns (
    category VARCHAR,
    records BIGINT
  )
);

-- The categories Jev may place a merchant in (UND-53): the Monarch labels in use in the run's
-- period. Left out: labels about moving money ("transfer", "payment": the transfer stage handles
-- those, and Monarch puts spending such as Venmo payments under them) and labels in Amex's
-- upload style ("Restaurant-Restaurant": a hyphen with no "Group: Name" colon), which are not
-- Monarch's own.
WITH labels AS (
  SELECT json_extract_string(monarch_raw, '$."Category"') AS category
  FROM etl.purchase_pairs
  WHERE monarch_raw IS NOT NULL
)
SELECT category, count(*) AS records
FROM labels
WHERE category IS NOT NULL
  AND trim(category) <> ''
  AND lower(category) NOT LIKE '%transfer%'
  AND lower(category) NOT LIKE '%payment%'
  AND NOT (regexp_matches(category, '[A-Za-z]-[A-Za-z]') AND category NOT LIKE '%: %')
GROUP BY category
ORDER BY category
