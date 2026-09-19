USE hdb_resale;

-- todo 1: price vs distance to MRT
SELECT
    COUNT(*) AS n,
    ROUND(AVG(to_mrt), 0) AS avg_to_mrt_m,
    ROUND(AVG(resale_price), 0) AS mean_price,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps
FROM v_geo_trx;

-- todo 2: price / pps by MRT distance band
SELECT
    mrt_band,
    COUNT(*) AS transactions,
    ROUND(AVG(to_mrt), 0) AS avg_to_mrt_m,
    ROUND(AVG(resale_price), 0) AS mean_price,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps,
    ROUND(AVG(floor_area_sqm), 1) AS mean_area
FROM v_geo_trx
GROUP BY mrt_band
ORDER BY MIN(to_mrt);

-- todo 3: price / pps by MRT distance band within a flat type
SET @flat = '4 ROOM';
SELECT
    mrt_band,
    COUNT(*) AS transactions,
    ROUND(AVG(resale_price), 0) AS mean_price,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps
FROM v_geo_trx
WHERE flat_type = @flat COLLATE utf8mb4_unicode_ci
GROUP BY mrt_band
ORDER BY MIN(to_mrt);

-- todo 4: top nearest_mrt stations by transaction volume
SELECT
    nearest_mrt,
    COUNT(*) AS transactions,
    ROUND(AVG(to_mrt), 0) AS avg_to_mrt_m,
    ROUND(AVG(resale_price), 0) AS mean_price,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps
FROM v_geo_trx
GROUP BY nearest_mrt
HAVING transactions >= 50
ORDER BY transactions DESC
LIMIT 25;

-- todo 5: highest pps stations
SELECT
    nearest_mrt,
    COUNT(*) AS transactions,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps,
    ROUND(AVG(to_mrt), 0) AS avg_to_mrt_m
FROM v_geo_trx
GROUP BY nearest_mrt
HAVING COUNT(*) >= 30
ORDER BY mean_pps DESC
LIMIT 20;
