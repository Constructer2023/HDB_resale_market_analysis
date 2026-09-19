DELIMITER $$
USE hdb_resale $$

-- Set some reusable variables
-- Set @cnt := (SELECT COUNT(*) FROM hdb_resale.resale_transactions) $$
-- Set @low_offset := FLOOR((@cnt + 1) / 2.0) - 1 $$
-- Set @high_offset := CEIL((@cnt + 1) / 2.0) - 1 $$

-- todo 1: median resale price
DROP FUNCTION IF EXISTS fn_median_resale_prices $$
CREATE FUNCTION fn_median_resale_prices()
RETURNS DECIMAL(12, 2)
READS SQL DATA
BEGIN
    DECLARE total_cnt INT;
    DECLARE low_offset INT;
    DECLARE high_offset INT;
    DECLARE med DECIMAL(12, 2);
    SELECT COUNT(*)
    INTO total_cnt
    FROM hdb_resale.resale_transactions;
    SET low_offset := FLOOR((total_cnt + 1) / 2.0) - 1;
    SET high_offset := CEIL((total_cnt + 1) / 2.0) - 1;
    SELECT AVG(sub.resale_price) INTO med
    FROM (
        (SELECT resale_price
         FROM hdb_resale.resale_transactions
         ORDER BY resale_price
         LIMIT 1
         OFFSET low_offset)
        UNION ALL
        (SELECT resale_price
         FROM hdb_resale.resale_transactions
         ORDER BY resale_price
         LIMIT 1
         OFFSET high_offset)
    ) AS sub;
    RETURN med;
END $$

-- todo 2: median floor_area_sqm
DROP FUNCTION IF EXISTS fn_median_floor_area_sqm $$
CREATE FUNCTION fn_median_floor_area_sqm()
RETURNS FLOAT
READS SQL DATA
BEGIN
    DECLARE total_cnt INT;
    DECLARE low_offset INT;
    DECLARE high_offset INT;
    DECLARE med FLOAT;
    SELECT COUNT(*)
    INTO total_cnt
    FROM hdb_resale.resale_transactions;
    SET low_offset := FLOOR((total_cnt + 1) / 2.0) - 1;
    SET high_offset := CEIL((total_cnt + 1) / 2.0) - 1;
    SELECT AVG(sub.floor_area_sqm) INTO med
    FROM (
        (SELECT floor_area_sqm
         FROM hdb_resale.resale_transactions
         ORDER BY floor_area_sqm
         LIMIT 1
         OFFSET low_offset)
        UNION ALL
        (SELECT floor_area_sqm
         FROM hdb_resale.resale_transactions
         ORDER BY floor_area_sqm
         LIMIT 1
         OFFSET high_offset)
    ) AS sub;
    RETURN med;
END $$

-- todo 3: median price_per_sqm
DROP FUNCTION IF EXISTS fn_median_price_per_sqm $$
CREATE FUNCTION fn_median_price_per_sqm()
RETURNS DECIMAL(10, 2)
READS SQL DATA
BEGIN
    DECLARE total_cnt INT;
    DECLARE low_offset INT;
    DECLARE high_offset INT;
    DECLARE med DECIMAL(10, 2);
    SELECT COUNT(*)
    INTO total_cnt
    FROM hdb_resale.resale_transactions;
    SET low_offset := FLOOR((total_cnt + 1) / 2.0) - 1;
    SET high_offset := CEIL((total_cnt + 1) / 2.0) - 1;
    SELECT AVG(sub.price_per_sqm) INTO med
    FROM (
        (SELECT price_per_sqm
         FROM hdb_resale.resale_transactions
         ORDER BY price_per_sqm
         LIMIT 1
         OFFSET low_offset)
        UNION ALL
        (SELECT price_per_sqm
         FROM hdb_resale.resale_transactions
         ORDER BY price_per_sqm
         LIMIT 1
         OFFSET high_offset)
    ) AS sub;
    RETURN med;
END $$

-- todo 4: market overview by date
DROP PROCEDURE IF EXISTS sgp_market_overview$$
CREATE PROCEDURE sgp_market_overview(IN sgp_year_from INT, IN sgp_year_to INT)
BEGIN
    SELECT
        COUNT(*) AS total_transactions,
        MIN(trx_date) AS earliest_date,
        MAX(trx_date) AS latest_date,
        ROUND(AVG(resale_price), 0) AS mean_price,
        ROUND(AVG(floor_area_sqm), 1) AS mean_area_sqm,
        ROUND(AVG(price_per_sqm), 0) AS mean_price_per_sqm
    FROM resale_transactions
    WHERE (sgp_year_from IS NULL OR trx_year >= sgp_year_from)
      AND (sgp_year_to IS NULL OR trx_year <= sgp_year_to);
END $$

-- todo 5: Return the specified percentage data
DROP FUNCTION IF EXISTS pct_data$$
CREATE FUNCTION pct_data(`rank` INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE target INT;
    SELECT
        id INTO target
    FROM
        order_by_price
    WHERE
        id = FLOOR((SELECT COUNT(*) FROM order_by_price) * `rank`);
    RETURN target;
END $$

-- todo 6: town ranking
DROP PROCEDURE IF EXISTS sgp_town_ranking$$
CREATE PROCEDURE sgp_town_ranking(IN min_trx INT, IN direction BOOLEAN, IN n_limit INT)
BEGIN
    IF direction THEN
        -- Sort highest to lowest
        SELECT
            town,
            COUNT(*) AS trxs,
            ROUND(AVG(resale_price), 2) AS mean_price,
            ROUND(AVG(price_per_sqm), 2) AS mean_pps
        FROM resale_transactions
        GROUP BY town
        HAVING trxs >= min_trx
        ORDER BY mean_price DESC
        LIMIT n_limit;
    ELSE
        -- Sort lowest to highest
        SELECT
            town,
            COUNT(*) AS trxs,
            ROUND(AVG(resale_price), 2) AS mean_price,
            ROUND(AVG(price_per_sqm), 2) AS mean_pps
        FROM resale_transactions
        GROUP BY town
        HAVING trxs >= min_trx
        ORDER BY mean_price ASC
        LIMIT n_limit;
    END IF;
END $$

-- todo 7: outliers
DROP PROCEDURE IF EXISTS price_outliers$$
CREATE PROCEDURE price_outliers(IN p_percentile DECIMAL(5, 4), IN p_high BOOLEAN)
BEGIN
    DECLARE cnt INT;
    DECLARE offset_val INT;
    SELECT COUNT(*) INTO cnt FROM resale_transactions;
    SET offset_val = FLOOR(cnt * IF(p_high, 1 - p_percentile, p_percentile));
    IF p_high THEN
        SELECT *
        FROM resale_transactions
        WHERE resale_price >= (
            SELECT resale_price
            FROM order_by_price
            LIMIT 1 OFFSET offset_val
        )
        ORDER BY resale_price DESC;
    ELSE
        SELECT *
        FROM resale_transactions
        WHERE resale_price <= (
            SELECT resale_price
            FROM order_by_price
            LIMIT 1 OFFSET offset_val
        )
        ORDER BY resale_price ASC;
    END IF;
END $$
