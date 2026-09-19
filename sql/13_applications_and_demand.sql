USE hdb_resale;

-- todo 1: total applications by year
SELECT
    year,
    SUM(num) AS total_applications
FROM resale_applications_by_flat_type
GROUP BY year
ORDER BY year;

-- todo 2: applications by flat type (latest year)
SELECT
    flat_type,
    SUM(num) AS applications
FROM resale_applications_by_flat_type
WHERE year = (SELECT MAX(year) FROM resale_applications_by_flat_type)
GROUP BY flat_type
ORDER BY applications DESC;

-- todo 3: quarterly applications trend (recent)
SELECT
    quarter,
    SUM(num) AS applications
FROM resale_applications_by_flat_type
WHERE year >= 2020
GROUP BY quarter
ORDER BY quarter;

-- todo 4: applications registered (resale vs rental) by financial year
SELECT
    year,
    SUM(CASE WHEN type = 'resale' THEN num ELSE 0 END) AS resale_apps,
    SUM(CASE WHEN type = 'rental' THEN num ELSE 0 END) AS rental_apps,
    SUM(num) AS total_apps
FROM applications_registered
GROUP BY year
ORDER BY year;

-- todo 5: historical demand
SELECT
    start_year,
    end_year,
    flat_type,
    demands
FROM demand_for_flats
ORDER BY start_year, flat_type;
