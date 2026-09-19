USE hdb_resale;

-- todo 1: Monthly overview data
CREATE OR REPLACE VIEW sgp_month_trend AS
    SELECT
        trx_year,
        trx_month,
        COUNT(*) AS total_trx,
        ROUND(AVG(resale_price), 0) AS mean_price,
        ROUND(AVG(floor_area_sqm), 0) AS mean_area,
        ROUND(AVG(price_per_sqm), 0) AS mean_pps
    FROM
        hdb_resale.resale_transactions
    GROUP BY trx_year, trx_month
    ORDER BY trx_year, trx_month;

-- todo 2: Data order by price
CREATE OR REPLACE VIEW order_by_price AS
    SELECT *
    FROM hdb_resale.resale_transactions
    ORDER BY resale_price;

-- todo 3: percentile value
CREATE OR REPLACE VIEW pct_rank AS
    SELECT
        1 AS pct0,
        FLOOR(COUNT(*) * 0.25) AS pct25,
        FLOOR(COUNT(*) * 0.5) AS pct50,
        CEIL(COUNT(*) * 0.75) AS pct75,
        CEIL(COUNT(*) * 0.95) AS pct95,
        COUNT(*) AS pct100
    FROM
        hdb_resale.resale_transactions;

-- todo 4: factor separated view
CREATE OR REPLACE VIEW factor_trxs AS
SELECT
    *,
    CASE
        WHEN floor_area_sqm < 60  THEN '<60'
        WHEN floor_area_sqm < 80  THEN '60-79'
        WHEN floor_area_sqm < 100 THEN '80-99'
        WHEN floor_area_sqm < 120 THEN '100-119'
        ELSE '120+'
    END AS area_band,
    CASE
        WHEN storey_midpoint <= 3  THEN '01-03'
        WHEN storey_midpoint <= 6  THEN '04-06'
        WHEN storey_midpoint <= 9  THEN '07-09'
        WHEN storey_midpoint <= 12 THEN '10-12'
        WHEN storey_midpoint <= 15 THEN '13-15'
        WHEN storey_midpoint <= 18 THEN '16-18'
        ELSE '19+'
    END AS storey_band,
    CASE
        WHEN flat_year < 10 THEN '0-9 yrs'
        WHEN flat_year < 20 THEN '10-19 yrs'
        WHEN flat_year < 30 THEN '20-29 yrs'
        WHEN flat_year < 40 THEN '30-39 yrs'
        ELSE '40+ yrs'
    END AS age_band,
    CASE
        WHEN remaining_lease_month < 600 THEN '<50 yrs'
        WHEN remaining_lease_month < 720 THEN '50-59 yrs'
        WHEN remaining_lease_month < 840 THEN '60-69 yrs'
        WHEN remaining_lease_month < 960 THEN '70-79 yrs'
        ELSE '80+ yrs'
    END AS lease_band
FROM hdb_resale.resale_transactions;

-- todo 5: latest median price per town & flat type
CREATE OR REPLACE VIEW latest_median_prices AS
SELECT
    year,
    town,
    flat_type,
    median_resale_price
FROM median_resale_prices AS m
WHERE year = (SELECT MAX(year) FROM median_resale_prices)
  AND median_resale_price <> 0;

-- todo 6: yearly average of the official resale price index
CREATE OR REPLACE VIEW yearly_avg_rpi AS
SELECT
    year,
    ROUND(AVG(rpi), 1) AS avg_rpi,
    ROUND(MIN(rpi), 1) AS min_rpi,
    ROUND(MAX(rpi), 1) AS max_rpi
FROM resale_price_index
GROUP BY year;

-- todo 7: combined quarterly applications (all flat types)
CREATE OR REPLACE VIEW quarterly_applications AS
SELECT
    year,
    quarter,
    SUM(num) AS total_applications
FROM resale_applications_by_flat_type
GROUP BY year, quarter;

-- todo 8: add bands
CREATE OR REPLACE VIEW v_geo_trx AS
SELECT
    *,
    ROUND(to_mrt / 1000, 2) AS to_mrt_km,
    ROUND(to_city / 1000, 2) AS to_city_km,
    CASE
        WHEN to_mrt < 300 THEN '0-299m'
        WHEN to_mrt < 500 THEN '300-499m'
        WHEN to_mrt < 800 THEN '500-799m'
        WHEN to_mrt < 1200 THEN '800-1199m'
        WHEN to_mrt < 2000 THEN '1.2-2km'
        ELSE '2km+'
    END AS mrt_band,
    CASE
        WHEN to_city < 5000  THEN '0-5km'
        WHEN to_city < 10000 THEN '5-10km'
        WHEN to_city < 15000 THEN '10-15km'
        WHEN to_city < 20000 THEN '15-20km'
        ELSE '20km+'
    END AS city_band
FROM
    resale_trx_geo
WHERE
    lat IS NOT NULL
  AND lon IS NOT NULL
  AND to_mrt IS NOT NULL
  AND to_city IS NOT NULL;
