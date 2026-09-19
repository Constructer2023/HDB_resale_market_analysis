USE hdb_resale;

-- todo 1: coverage of geo fields
SELECT
    COUNT(*) AS total_rows,
    SUM(lat IS NULL) AS missing_lat,
    SUM(lon IS NULL) AS missing_lon,
    SUM(postal IS NULL OR postal = 'NIL') AS missing_postal,
    SUM(zone_id IS NULL) AS missing_zone_id,
    SUM(to_mrt IS NULL) AS missing_to_mrt,
    SUM(to_city IS NULL) AS missing_to_city,
    SUM(nearest_mrt IS NULL) AS missing_nearest_mrt,
    ROUND(100 * SUM(lat IS NOT NULL) / COUNT(*), 1) AS pct_geocoded
FROM resale_trx_geo;

-- todo 2: extreme distances, possible errors
SELECT id, blk, st, subzone, lat, lon, to_mrt, to_city, nearest_mrt, resale_price
FROM resale_trx_geo
WHERE to_mrt > 5000 OR to_city > 35000
ORDER BY to_mrt DESC
LIMIT 50;

-- todo 3: subzones with very few points, unstable for modelling
SELECT subzone, zone_id, COUNT(*) AS n
FROM resale_trx_geo
WHERE subzone IS NOT NULL
GROUP BY subzone, zone_id
HAVING COUNT(*) < 20
ORDER BY n;
