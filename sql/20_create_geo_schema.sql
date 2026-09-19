USE hdb_resale;

SET GLOBAL local_infile = 1;

DROP TABLE IF EXISTS resale_transactions_geoready;
CREATE TABLE resale_transactions_geoready(
    id INT AUTO_INCREMENT PRIMARY KEY,
    trx_date DATE,
    trx_year INT,
    trx_month INT,
    lease_commence INT,
    flat_year INT,
    remaining_lease_month INT,
    flat_type VARCHAR(20),
    flat_model VARCHAR(30),
    town VARCHAR(30),
    st VARCHAR(50),
    blk VARCHAR(10),
    storey_lower SMALLINT,
    storey_midpoint SMALLINT,
    storey_upper SMALLINT,
    price_per_sqm DECIMAL(10, 2),
    floor_area_sqm FLOAT,
    resale_price DECIMAL(12, 2)
) ENGINE = InnoDB COMMENT 'resale transactions table for join';
LOAD DATA LOCAL INFILE './data/processed/resale_transactions.csv'
    INTO TABLE resale_transactions_geoready
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES(
        trx_date,
        trx_year,
        trx_month,
        lease_commence,
        flat_year,
        remaining_lease_month,
        flat_type,
        flat_model,
        town,
        st,
        blk,
        storey_lower,
        storey_midpoint,
        storey_upper,
        price_per_sqm,
        floor_area_sqm,
        resale_price
);
DROP TABLE IF EXISTS geocode_cache;
CREATE TABLE geocode_cache(
    id INT AUTO_INCREMENT PRIMARY KEY,
    blk VARCHAR(10),
    st VARCHAR(50),
    search_val VARCHAR(60),
    lat DOUBLE,
    lon DOUBLE,
    postal VARCHAR(10),
    subzone VARCHAR(50),
    zone_id INT,
    nearest_mrt VARCHAR(50),
    mrt_lat DOUBLE,
    mrt_lon DOUBLE,
    to_mrt DOUBLE,
    to_city DOUBLE,
    status VARCHAR(20)
) ENGINE = InnoDB COMMENT 'geocode cache table for join';
LOAD DATA LOCAL INFILE './data/aid/hdb_geocode_cache.csv'
    INTO TABLE geocode_cache
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES(
        blk,
        st,
        search_val,
        lat,
        lon,
        postal,
        subzone,
        zone_id,
        nearest_mrt,
        mrt_lat,
        mrt_lon,
        to_mrt,
        to_city,
        status
);
DROP TABLE IF EXISTS resale_trx_geo;
CREATE TABLE resale_trx_geo AS
    SELECT
        t1.*,
        t2.search_val,
        t2.lat,
        t2.lon,
        t2.postal,
        t2.subzone,
        t2.zone_id,
        t2.nearest_mrt,
        t2.mrt_lat,
        t2.mrt_lon,
        t2.to_mrt,
        t2.to_city,
        t2.status
    FROM
        resale_transactions_geoready AS t1
    LEFT JOIN geocode_cache AS t2
        ON t1.blk = t2.blk
        AND t1.st = t2.st;
ALTER TABLE resale_trx_geo
    DROP COLUMN storey_lower,
    DROP COLUMN storey_upper,
    DROP COLUMN town;
