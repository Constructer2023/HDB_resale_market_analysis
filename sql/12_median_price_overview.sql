USE hdb_resale;

SET @year_from = 2017;
SET @min_trx_proxy = 1;

-- todo 1: latest quarters snapshot by town
SELECT
    town,
    ROUND(AVG(median_resale_price), 2) AS avg_median_price,
    COUNT(*) AS flat_type_rows
FROM median_resale_prices
WHERE year = (SELECT MAX(year) FROM median_resale_prices)
  AND median_resale_price <> 0
GROUP BY town
ORDER BY avg_median_price DESC;

-- todo 2: median price trend for a specific town & flat type
SET @town = 'CENTRAL AREA';
SET @flat = '3 ROOM';

SELECT
    year,
    quarter,
    median_resale_price
FROM median_resale_prices
WHERE town = @town COLLATE utf8mb4_0900_ai_ci
  AND flat_type = @flat COLLATE utf8mb4_0900_ai_ci
  AND (@year_from IS NULL OR year >= @year_from)
ORDER BY year, quarter;

-- todo 3: most expensive town-flat combinations in latest quarter
SELECT
    trx_quarter_year,
    town,
    flat_type,
    median_resale_price
FROM median_resale_prices
WHERE year = (SELECT MAX(year) FROM median_resale_prices)
  AND median_resale_price <> 0
ORDER BY median_resale_price DESC
LIMIT 20;

-- todo 4: yearly average median price by flat type
SELECT
    year,
    flat_type,
    ROUND(AVG(median_resale_price), 2) AS avg_median_price
FROM median_resale_prices
WHERE median_resale_price <> 0
  AND (@year_from IS NULL OR year >= @year_from)
GROUP BY year, flat_type
ORDER BY year, flat_type;
