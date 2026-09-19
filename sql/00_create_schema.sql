CREATE DATABASE IF NOT EXISTS hdb_resale
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hdb_resale;

DROP TABLE IF EXISTS resale_transactions;

CREATE TABLE resale_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trx_date DATE,
    trx_year INT CHECK (trx_year >= 1965),
    trx_month INT CHECK(trx_month >= 1 AND trx_month <= 12),
    lease_commence INT CHECK (lease_commence >= 1965),
    flat_year INT CHECK(flat_year >= 0),
    remaining_lease_month INT CHECK (remaining_lease_month <= 99 * 12),
    flat_type VARCHAR(20),
    flat_model VARCHAR(30),
    town VARCHAR(30),
    street_name VARCHAR(40),
    block VARCHAR(4),
    storey_lower SMALLINT CHECK (storey_lower >= 1),
    storey_midpoint SMALLINT CHECK (storey_midpoint >= 1),
    storey_upper SMALLINT CHECK(storey_upper >= 1),
    price_per_sqm DECIMAL(10, 2) CHECK(price_per_sqm > 0),
    floor_area_sqm FLOAT CHECK (floor_area_sqm > 0),
    resale_price DECIMAL(12, 2) CHECK(resale_price > 0)
) ENGINE = InnoDB COMMENT 'Primary table for analysis';

SET GLOBAL local_infile = 1;
LOAD DATA LOCAL INFILE './data/processed/resale_transactions.csv'
    INTO TABLE resale_transactions
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES(
        trx_date, trx_year, trx_month, lease_commence, flat_year, remaining_lease_month,
        flat_type, flat_model, town, street_name, block, storey_lower, storey_midpoint, storey_upper,
        price_per_sqm, floor_area_sqm, resale_price
);

SELECT count(*) AS number_of_records
FROM resale_transactions;

SELECT *
FROM resale_transactions
LIMIT 10;

ALTER TABLE resale_transactions
    ADD INDEX idx_trx_date(trx_date),
    ADD INDEX idx_location(town, street_name, block),
    ADD INDEX idx_flat_type(flat_type),
    ADD INDEX idx_resale_price(resale_price);
