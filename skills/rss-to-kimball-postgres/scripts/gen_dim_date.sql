-- scripts/gen_dim_date.sql
-- Idempotent. Generates dim_date for 2000-01-01 .. 2050-12-31.
-- Re-running is a no-op thanks to ON CONFLICT.

INSERT INTO dim_date (
  date_key, full_date, year, quarter, month, day,
  iso_year, iso_week, day_of_week, is_weekend
)
SELECT
  to_char(d, 'YYYYMMDD')::int                     AS date_key,
  d                                                AS full_date,
  extract(year     FROM d)::smallint              AS year,
  extract(quarter  FROM d)::smallint              AS quarter,
  extract(month    FROM d)::smallint              AS month,
  extract(day      FROM d)::smallint              AS day,
  extract(isoyear  FROM d)::smallint              AS iso_year,
  extract(week     FROM d)::smallint              AS iso_week,
  extract(isodow   FROM d)::smallint              AS day_of_week,
  extract(isodow   FROM d) IN (6, 7)              AS is_weekend
FROM generate_series('2000-01-01'::date,
                     '2050-12-31'::date,
                     '1 day') AS d
ON CONFLICT (date_key) DO NOTHING;
