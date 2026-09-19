USE hdb_resale;

SET @year_from = NULL;
SET @year_to = NULL;
-- todo 1: overall market snapshot
CALL sgp_market_overview(@year_from, @year_to);

-- todo 2: median values for each price metrics
SELECT
    fn_median_resale_prices() AS median_resale_price,
    fn_median_floor_area_sqm() AS median_floor_area,
    fn_median_price_per_sqm() AS median_price_per_sqm;
