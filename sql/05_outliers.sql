USE hdb_resale;

SET @pct = 0.005;
SET @year_from = 2017;
SET @year_to = 2026;

-- todo 1: too high price
CALL price_outliers(@pct, TRUE);

-- todo 2: too low price
CALL price_outliers(@pct, FALSE);

-- todo 3: high unit price outliers
WITH filtered_trxs AS (
    SELECT *, PERCENT_RANK() OVER (ORDER BY price_per_sqm ASC) AS pct_rank
    FROM resale_transactions
    WHERE (@year_from IS NULL OR trx_year >= @year_from)
      AND (@year_to IS NULL OR trx_year <= @year_to)
)
SELECT *
FROM filtered_trxs
WHERE pct_rank >= (1 - @pct)
ORDER BY price_per_sqm DESC;
