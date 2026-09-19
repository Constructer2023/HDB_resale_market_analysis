USE hdb_resale;

SET GLOBAL local_infile = 1;

DROP TABLE IF EXISTS resale_price_index;
CREATE TABLE resale_price_index (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trx_quarter_year VARCHAR(7) NOT NULL,
    rpi DECIMAL(6, 1)
) ENGINE = InnoDB COMMENT = 'HDB Resale Price Index by quarter (long form)';
CREATE INDEX idx_trx_quarter_year ON resale_price_index (trx_quarter_year);
LOAD DATA LOCAL INFILE './data/processed/resale_price_index.csv'
    INTO TABLE resale_price_index
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES(
        trx_quarter_year,
        rpi
);
ALTER TABLE resale_price_index
ADD COLUMN year INT,
ADD COLUMN quarter INT;
UPDATE resale_price_index SET
    year = CAST(LEFT(trx_quarter_year, 4) AS UNSIGNED),
    quarter = CAST(RIGHT(trx_quarter_year, 1) AS UNSIGNED)
WHERE trx_quarter_year IS NOT NULL;
ALTER TABLE resale_price_index
    ADD INDEX idx_year(year),
    ADD INDEX idx_quarter(quarter);


DROP TABLE IF EXISTS median_resale_prices;
CREATE TABLE median_resale_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trx_quarter_year VARCHAR(7) NOT NULL,
    town VARCHAR(30) NOT NULL,
    flat_type VARCHAR(20) NOT NULL,
    median_resale_price DECIMAL(12, 2)
) ENGINE = InnoDB COMMENT = 'Official median resale prices by town and flat type (quarterly)';
LOAD DATA LOCAL INFILE './data/processed/median_resale_prices.csv'
    INTO TABLE median_resale_prices
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES(
        trx_quarter_year,
        town,
        flat_type,
        median_resale_price
);
ALTER TABLE median_resale_prices
ADD COLUMN year INT,
ADD COLUMN quarter INT;
UPDATE median_resale_prices SET
    year = CAST(LEFT(trx_quarter_year, 4) AS UNSIGNED),
    quarter = CAST(RIGHT(trx_quarter_year, 1) AS UNSIGNED)
WHERE trx_quarter_year IS NOT NULL;
ALTER TABLE median_resale_prices
    ADD INDEX idx_trx_quarter_year(trx_quarter_year),
    ADD INDEX idx_year(year),
    ADD INDEX idx_quarter(quarter),
    ADD INDEX idx_town(town),
    ADD INDEX idx_flat_type(flat_type);


DROP TABLE IF EXISTS resale_applications_by_flat_type;
CREATE TABLE resale_applications_by_flat_type (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trx_quarter_year VARCHAR(7) NOT NULL,
    flat_type VARCHAR(20) NOT NULL,
    num INT
) ENGINE = InnoDB COMMENT = 'Number of resale applications registered by flat type (quarterly)';
LOAD DATA LOCAL INFILE './data/processed/resale_applications_by_flat_type.csv'
    INTO TABLE resale_applications_by_flat_type
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES(
        trx_quarter_year,
        flat_type,
        num
);
ALTER TABLE resale_applications_by_flat_type
ADD COLUMN year INT,
ADD COLUMN quarter INT;
UPDATE resale_applications_by_flat_type SET
    year = CAST(LEFT(trx_quarter_year, 4) AS UNSIGNED),
    quarter = CAST(RIGHT(trx_quarter_year, 1) AS UNSIGNED)
WHERE trx_quarter_year IS NOT NULL;
ALTER TABLE resale_applications_by_flat_type
    ADD INDEX idx_trx_quarter_year(trx_quarter_year),
    ADD INDEX idx_year(year),
    ADD INDEX idx_quarter(quarter),
    ADD INDEX idx_flat_type(flat_type);


DROP TABLE IF EXISTS applications_registered;
CREATE TABLE applications_registered (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year SMALLINT NOT NULL,
    type VARCHAR(10) NOT NULL,
    num INT
) ENGINE = InnoDB COMMENT = 'Applications registered for resale and rental flats by financial year';
LOAD DATA LOCAL INFILE './data/processed/applications_registered.csv'
    INTO TABLE applications_registered
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES(
        year,
        type,
        num
);
ALTER TABLE applications_registered
    ADD INDEX idx_year(year),
    ADD INDEX idx_type(type);


DROP TABLE IF EXISTS demand_for_flats;
CREATE TABLE demand_for_flats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    start_year SMALLINT NOT NULL,
    end_year SMALLINT NOT NULL,
    flat_type VARCHAR(30) NOT NULL,
    demands INT,
    mid_year SMALLINT
) ENGINE = InnoDB COMMENT = 'Historical demand for rental and home-ownership flats by period';
LOAD DATA LOCAL INFILE './data/processed/demand_for_flats.csv'
    INTO TABLE demand_for_flats
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES(
        start_year,
        end_year,
        flat_type,
        demands,
        mid_year
);
ALTER TABLE demand_for_flats
    ADD INDEX idx_mid_year(mid_year),
    ADD INDEX idx_flat_type(flat_type);
