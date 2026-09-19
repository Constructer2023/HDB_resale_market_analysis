USE hdb_resale;

SET @year_from = NULL;
SET @year_to = NULL;

-- todo 1: most expensive towns
CALL sgp_town_ranking(100, TRUE, 3);

-- todo 2: least expensive towns
CALL sgp_town_ranking(100, FALSE, 3);

-- todo 3: flat type data shredding
SELECT
    flat_type,
    trx_year,
    COUNT(*) AS number_of_trx,
    ROUND(AVG(resale_price), 2) AS mean_price,
    ROUND(AVG(floor_area_sqm), 1) AS mean_area,
    ROUND(AVG(price_per_sqm), 2) AS mean_pps
FROM
    resale_transactions
GROUP BY
    flat_type, trx_year
ORDER BY
    mean_price DESC;

-- todo 4: area vs price
SELECT
    area_band,
    COUNT(*) AS number_of_trxs,
    ROUND(AVG(resale_price), 2) AS mean_price,
    ROUND(AVG(price_per_sqm), 2) AS mean_pps
FROM
    factor_trxs
WHERE
    (trx_year >= @year_from OR @year_from IS NULL)
  AND (trx_year <= @year_to OR @year_to IS NULL)
GROUP BY
    area_band
ORDER BY
    number_of_trxs DESC;

-- todo 5: age vs price
SELECT
    age_band,
    COUNT(*) AS number_of_trxs,
    ROUND(AVG(resale_price), 2) AS mean_price,
    ROUND(AVG(price_per_sqm), 2) AS mean_pps,
    ROUND(AVG(floor_area_sqm), 1) AS mean_area
FROM
    factor_trxs
WHERE
    (trx_year >= @year_from OR @year_from IS NULL)
  AND (trx_year <= @year_to OR @year_to IS NULL)
GROUP BY
    age_band
ORDER BY
    number_of_trxs DESC;

-- todo 6: remaining lease vs price
SELECT
    lease_band,
    COUNT(*) AS number_of_trxs,
    ROUND(AVG(resale_price), 2) AS mean_price,
    ROUND(AVG(price_per_sqm), 2) AS mean_pps,
    ROUND(AVG(floor_area_sqm), 1) AS mean_area
FROM
    factor_trxs
WHERE
    (trx_year >= @year_from OR @year_from IS NULL)
  AND (trx_year <= @year_to OR @year_to IS NULL)
GROUP BY
    lease_band
ORDER BY
    number_of_trxs DESC;

-- todo 7: unit price by towns
SELECT
    town,
    COUNT(*) AS number_of_trxs,
    ROUND(AVG(price_per_sqm), 2) AS mean_pps
FROM
    resale_transactions
WHERE
    (trx_year >= @year_from OR @year_from IS NULL)
  AND (trx_year <= @year_to OR @year_to IS NULL)
GROUP BY
    town
HAVING
    number_of_trxs >= 50
ORDER BY
    mean_pps DESC;

-- todo 8: unit price by flat types
SELECT
    flat_type,
    COUNT(*) AS number_of_trxs,
    ROUND(AVG(price_per_sqm), 2) AS mean_pps
FROM
    resale_transactions
WHERE
    (trx_year >= @year_from OR @year_from IS NULL)
  AND (trx_year <= @year_to OR @year_to IS NULL)
GROUP BY
    flat_type
HAVING
    number_of_trxs >= 50
ORDER BY
    mean_pps DESC;
