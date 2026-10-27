MODEL (
  name etl.raw_amex,
  kind FULL,
  columns (
    source_row_number INT,
    source VARCHAR,
    transaction_date DATE,
    amount DECIMAL(18, 2),
    merchant VARCHAR,
    raw_record VARCHAR
  )
);

SELECT
  source_row_number,
  source,
  TRY_CAST(transaction_date AS DATE) AS transaction_date,
  CASE
    WHEN regexp_matches(trim(CAST(amount AS VARCHAR)), '^[(].*[)]$')
      THEN -TRY_CAST(regexp_replace(trim(CAST(amount AS VARCHAR)), '[^0-9.]', '', 'g') AS DECIMAL(18, 2))
    ELSE TRY_CAST(regexp_replace(trim(CAST(amount AS VARCHAR)), '[^0-9.-]', '', 'g') AS DECIMAL(18, 2))
  END AS amount,
  trim(CAST(merchant AS VARCHAR)) AS merchant,
  to_json(raw_record) AS raw_record
FROM read_json_auto(@amex_jsonl, format = 'newline_delimited')
