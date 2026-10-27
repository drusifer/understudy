MODEL (
  name etl.us_federal_holidays,
  kind SEED (
    path '../seeds/us_federal_holidays.csv'
  ),
  columns (
    holiday_date DATE,
    holiday_name VARCHAR
  )
);
