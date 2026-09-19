USE hdb_resale;

-- Helper: a quarterly summary of actual transactions
DROP TABLE IF EXISTS tmp_trx_quarterly;
CREATE TABLE tmp_trx_quarterly AS
SELECT
    trx_year,
    QUARTER(trx_date) AS trx_qtr,
    COUNT(*) AS volume,
    ROUND(AVG(resale_price), 2) AS mean_price,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps
FROM resale_transactions
GROUP BY trx_year, trx_qtr;
ALTER TABLE tmp_trx_quarterly
ADD COLUMN trx_period VARCHAR(7);
UPDATE tmp_trx_quarterly SET trx_period = CONCAT(trx_year, 'Q', trx_qtr);

-- todo 1: quarterly transaction mean price vs official resale price index
SELECT
    t.trx_period,
    t.volume,
    t.mean_price AS trx_mean_price,
    r.rpi AS official_rpi,
    ROUND(t.mean_price / rpi, 1)  AS price_to_index_ratio
FROM tmp_trx_quarterly AS t
INNER JOIN resale_price_index AS r
  ON t.trx_period = r.trx_quarter_year
ORDER BY t.trx_year, t.trx_qtr;

-- todo 2: quarterly transaction volume vs resale applications
SELECT
    t.trx_year,
    t.trx_qtr,
    t.volume AS actual_transactions,
    a.total_applications AS resale_applications,
    ROUND(t.volume * 100.0 / a.total_applications, 1) AS conversion_pct
FROM tmp_trx_quarterly AS t
JOIN (
    SELECT
        year,
        SUM(num) AS total_applications
    FROM resale_applications_by_flat_type
    GROUP BY year
) AS a ON t.trx_year = a.year
ORDER BY t.trx_year, t.trx_qtr;

-- todo 3: quarterly price-per-sqm trend by flat type
SELECT
    trx_year,
    QUARTER(trx_date) AS trx_qtr,
    flat_type,
    COUNT(*) AS transactions,
    ROUND(AVG(price_per_sqm), 2) AS mean_pps,
    ROUND(AVG(resale_price), 2) AS mean_price,
    ROUND(AVG(floor_area_sqm), 1) AS mean_area
FROM resale_transactions
GROUP BY trx_year, trx_qtr, flat_type
ORDER BY trx_year, trx_qtr, flat_type;

-- todo 4: annual resale application activity 2020–2025
SELECT
    year,
    SUM(num) AS total_resale_applications
FROM resale_applications_by_flat_type
WHERE year BETWEEN 2020 AND 2025
GROUP BY year
ORDER BY year;

/*
LIMITATIONS AND DATA CAVEATS
----------------------------

1. Different time coverage
   - resale_transactions: mainly 2017 onwards (registration date)
   - resale_price_index: long history back to 1990s
   - median_resale_prices: from ~2007-Q2
   - resale_applications_by_flat_type: from 2007-Q1
   - applications_registered: financial year, 2007–2024
   - demand_for_flats: multi-year blocks (1960s–2024)

2. Different definitions
   - “Median price” in median_resale_prices = official HDB median of registered applications
   - Median / mean in resale_transactions = calculated from completed resale transactions
   - These two series are related but not identical (timing, sample, exclusions differ).

3. Different frequencies / grains
   - Transactions: daily / monthly → aggregated to quarter for comparison
   - Official index & medians: already quarterly
   - applications_registered: annual (financial year)
   - demand_for_flats: multi-year periods only

4. Category standardisation
   - Town and flat_type have been upper-cased and normalised,
     but residual mismatches can still appear when joining.

5. Missing values
   - Official median table contains many “na” / “-” (especially 1-room / 2-room / Executive
     in certain towns). These were converted to NULL or zero value and excluded from comparisons.

6. Approximate medians
   - Exact median on the full transactions table is very expensive in pure SQL.
     Some queries use mean or a simplified median approximation.
     For publication-quality medians, prefer computing them in Python and loading a summary table.

7. Join coverage
   - Only quarters / town-flat combinations present in BOTH datasets appear in the
     comparison queries. Early or sparse periods may be under-represented.
*/
