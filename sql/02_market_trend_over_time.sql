USE hdb_resale;

SET @year_from = 2017;
SET @year_to   = NULL;

-- todo 1: Yearly trend
WITH temp AS (SELECT
    trx_year AS year,
    trx_month AS month,
    total_trx,
    mean_price * total_trx AS sum_up_price,
    mean_area * total_trx AS sum_up_area,
    mean_pps * total_trx AS sum_up_pps
FROM
    sgp_month_trend
)
SELECT
    year AS trx_year,
    ROUND(SUM(sum_up_price) / SUM(total_trx), 2) AS mean_price,
    ROUND(SUM(sum_up_area) / SUM(total_trx), 1) AS mean_area,
    ROUND(SUM(sum_up_pps) / SUM(total_trx), 2) AS mean_pps
FROM
    temp
GROUP BY
    trx_year
ORDER BY
    trx_year;

-- todo 2: Monthly trend
SELECT * FROM sgp_month_trend;

-- todo 3: Year-on-year change
SELECT
    trx_year,
    trx_month,
    ROUND((total_trx - LAG(total_trx, 12) OVER (ORDER BY trx_year, trx_month)) * 100 /
          LAG(total_trx, 12) OVER (ORDER BY trx_year, trx_month), 2)  AS trx_pct,
    ROUND((mean_price - LAG(mean_price, 12) OVER (ORDER BY trx_year, trx_month)) * 100 /
          LAG(mean_price, 12) OVER (ORDER BY trx_year, trx_month), 2) AS price_pct,
    ROUND((mean_area - LAG(mean_area, 12) OVER (ORDER BY trx_year, trx_month)) * 100 /
          LAG(mean_area, 12) OVER (ORDER BY trx_year, trx_month), 2)  AS area_pct,
    ROUND((mean_pps - LAG(mean_pps, 12) OVER (ORDER BY trx_year, trx_month)) * 100 /
          LAG(mean_pps, 12) OVER (ORDER BY trx_year, trx_month), 2)   AS pps_pct
FROM
    sgp_month_trend
ORDER BY
    trx_year, trx_month;

-- todo 4: Month-on-month change
SELECT
    trx_year,
    trx_month,
    ROUND((total_trx - LAG(total_trx) OVER (ORDER BY trx_year, trx_month)) * 100 /
          LAG(total_trx) OVER (ORDER BY trx_year, trx_month), 2)  AS trx_pct,
    ROUND((mean_price - LAG(mean_price) OVER (ORDER BY trx_year, trx_month)) * 100 /
          LAG(mean_price) OVER (ORDER BY trx_year, trx_month), 2) AS price_pct,
    ROUND((mean_area - LAG(mean_area) OVER (ORDER BY trx_year, trx_month)) * 100 /
          LAG(mean_area) OVER (ORDER BY trx_year, trx_month), 2)  AS area_pct,
    ROUND((mean_pps - LAG(mean_pps) OVER (ORDER BY trx_year, trx_month)) * 100 /
          LAG(mean_pps) OVER (ORDER BY trx_year, trx_month), 2)   AS pps_pct
FROM
    sgp_month_trend
ORDER BY
    trx_year, trx_month;
