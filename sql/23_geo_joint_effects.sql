USE hdb_resale;

-- todo 1: MRT band * city band
SELECT
    city_band,
    mrt_band,
    COUNT(*) AS transactions,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps,
    ROUND(AVG(resale_price), 0) AS mean_price
FROM v_geo_trx
GROUP BY city_band, mrt_band
HAVING transactions >= 20
ORDER BY AVG(to_city), AVG(to_mrt);

-- todo 2: within 1 km of MRT, does city distance still matter?
SELECT
    city_band,
    COUNT(*) AS transactions,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps,
    ROUND(AVG(resale_price), 0) AS mean_price
FROM v_geo_trx
WHERE to_mrt <= 1000
GROUP BY city_band
ORDER BY MIN(to_city);

-- todo 3: far from MRT (>1.2 km), price penalty by flat type
SELECT
    flat_type,
    COUNT(*) AS transactions,
    ROUND(AVG(to_mrt), 0) AS avg_to_mrt_m,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps
FROM v_geo_trx
WHERE to_mrt > 1200
GROUP BY flat_type
ORDER BY mean_pps DESC;

-- todo 4: simple correlation proxies, compare extremes
SELECT
    'near_mrt_<500m' AS segment,
    ROUND(AVG(price_per_sqm), 0) AS 'mean_pps',
    COUNT(*) AS 'n'
FROM v_geo_trx
WHERE to_mrt < 500
UNION ALL
SELECT
    'far_mrt_>1500m',
    ROUND(AVG(price_per_sqm), 0) AS 'mean_pps',
    COUNT(*) AS 'n'
FROM v_geo_trx
WHERE to_mrt > 1500
UNION ALL
SELECT
    'near_city_<8km',
    ROUND(AVG(price_per_sqm), 0) AS 'mean_pps',
    COUNT(*) AS 'n'
FROM v_geo_trx
WHERE to_city < 8000
UNION ALL
SELECT
    'far_city_>18km',
    ROUND(AVG(price_per_sqm), 0) AS 'mean_pps',
    COUNT(*) AS 'n'
FROM v_geo_trx
WHERE to_city > 18000;
