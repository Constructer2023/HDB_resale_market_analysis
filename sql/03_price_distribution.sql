USE hdb_resale;

SET @year_from = NULL;
SET @year_to = NULL;

-- todo 1: key percentiles
SELECT ROUND(MIN(resale_price), 2)                                                                 AS pct0,
       ROUND((SELECT resale_price
              FROM order_by_price
              WHERE id = (SELECT pct25
                          FROM pct_rank)), 2) AS pct25,
       ROUND((SELECT resale_price
              FROM order_by_price
              WHERE id = (SELECT pct50
                          FROM pct_rank)), 2) AS pct50,
       ROUND((SELECT resale_price
              FROM order_by_price
              WHERE id = (SELECT pct75
                          FROM pct_rank)), 2) AS pct75,
       ROUND((SELECT resale_price
              FROM order_by_price
              WHERE id = (SELECT pct95
                          FROM pct_rank)), 2) AS pct95,
       ROUND(MAX(resale_price), 2)                                                                 AS pct100
FROM resale_transactions;

-- todo 2: price bands
SELECT
    CASE
        WHEN resale_price < 300000 THEN '<300k'
        WHEN resale_price < 400000 THEN '300k-399k'
        WHEN resale_price < 500000 THEN '400k-499k'
        WHEN resale_price < 600000 THEN '500k-599k'
        WHEN resale_price < 700000 THEN '600k-699k'
        WHEN resale_price < 800000 THEN '700k-799k'
        WHEN resale_price < 1000000 THEN '800k-1M'
        ELSE '1M+'
    END AS price_band,
    COUNT(*) AS total_trx,
    ROUND(COUNT(*) * 100 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM
    resale_transactions
WHERE
    (trx_year >= @year_from OR @year_from IS NULL)
  AND (trx_year <= @year_to OR @year_to IS NULL)
GROUP BY
    price_band
ORDER BY
    MAX(resale_price);
