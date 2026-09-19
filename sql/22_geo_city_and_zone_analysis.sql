USE hdb_resale;

-- todo 1: price vs distance to city centre
SELECT
    city_band,
    COUNT(*) AS transactions,
    ROUND(AVG(to_city), 0) AS avg_to_city_m,
    ROUND(AVG(resale_price), 0) AS mean_price,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps
FROM v_geo_trx
GROUP BY city_band
ORDER BY MIN(to_city);

-- todo 2: by planning area / subzone
SELECT
    zone_id,
    subzone,
    COUNT(*) AS transactions,
    ROUND(AVG(to_mrt), 0) AS avg_to_mrt_m,
    ROUND(AVG(to_city), 0) AS avg_to_city_m,
    ROUND(AVG(resale_price), 0) AS mean_price,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps
FROM v_geo_trx
WHERE zone_id IS NOT NULL
GROUP BY zone_id, subzone
HAVING transactions >= 30
ORDER BY mean_pps DESC
LIMIT 30;

-- todo 3: cheapest subzones by pps
SELECT
    zone_id,
    subzone,
    COUNT(*) AS transactions,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps,
    ROUND(AVG(to_city), 0) AS avg_to_city_m
FROM v_geo_trx
WHERE zone_id IS NOT NULL
GROUP BY zone_id, subzone
HAVING COUNT(*) >= 30
ORDER BY mean_pps ASC
LIMIT 20;

-- todo 4: zone_id as model-style feature, yearly mean pps
SELECT
    trx_year,
    zone_id,
    subzone,
    COUNT(*) AS transactions,
    ROUND(AVG(price_per_sqm), 0) AS mean_pps
FROM v_geo_trx
WHERE zone_id IS NOT NULL
  AND trx_year >= 2017
GROUP BY trx_year, zone_id, subzone
HAVING transactions >= 20
ORDER BY trx_year, mean_pps DESC;
