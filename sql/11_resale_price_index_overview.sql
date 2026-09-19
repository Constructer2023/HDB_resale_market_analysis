USE hdb_resale;

SET @year_from = 2010;
SET @year_to = NULL;

-- todo 1: overall market context snapshot
SELECT
    MIN(year) AS earliest,
    MAX(year) AS latest,
    MIN(rpi) AS min_index,
    MAX(rpi) AS max_index,
    ROUND(AVG(rpi), 1) AS avg_index
FROM resale_price_index
WHERE (@year_from IS NULL OR year >= @year_from)
  AND (@year_to   IS NULL OR year <= @year_to);

-- todo 2: index by year (average of the 4 quarters)
SELECT
    year,
    ROUND(AVG(rpi), 1) AS avg_index,
    ROUND(MIN(rpi), 1) AS min_index,
    ROUND(MAX(rpi), 1) AS max_index
FROM resale_price_index
WHERE (@year_from IS NULL OR year >= @year_from)
  AND (@year_to   IS NULL OR year <= @year_to)
GROUP BY year
ORDER BY year;

-- todo 3: quarter-on-quarter change
SELECT
    curr.year,
    curr.quarter,
    curr.rpi AS curr_index,
    prev.rpi AS prev_index,
    ROUND(curr.rpi - prev.rpi, 1) AS qoq_change,
    ROUND((curr.rpi - prev.rpi) * 100.0 / prev.rpi, 2) AS qoq_pct
FROM resale_price_index AS curr
LEFT JOIN resale_price_index AS prev
       ON prev.year = IF(curr.quarter = 1, curr.year - 1, curr.year)
      AND prev.quarter = IF(curr.quarter = 1, 4, curr.quarter - 1)
WHERE (@year_from IS NULL OR curr.year >= @year_from)
ORDER BY curr.year, curr.quarter;

-- todo 4: recent 12 quarters
SELECT year, quarter, rpi
FROM resale_price_index
ORDER BY year DESC, quarter DESC
LIMIT 12;
