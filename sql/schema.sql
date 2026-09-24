-- Warehouse schema for the e-commerce market intelligence pipeline.
-- Applied automatically by warehouse/load_postgres.py (CREATE TABLE IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS products (
    product_key   VARCHAR(16)  NOT NULL,
    source        VARCHAR(50)  NOT NULL,
    product_id    VARCHAR(64),
    name          TEXT         NOT NULL,
    category      VARCHAR(100),
    url           TEXT,
    stock_status  VARCHAR(50),
    first_seen    DATE         NOT NULL,
    last_seen     DATE         NOT NULL,
    PRIMARY KEY (product_key, source)
);

CREATE TABLE IF NOT EXISTS price_history (
    product_key          VARCHAR(16)      NOT NULL,
    source               VARCHAR(50)      NOT NULL,
    snapshot_date        DATE             NOT NULL,
    min_price            DOUBLE PRECISION NOT NULL,
    avg_price            DOUBLE PRECISION NOT NULL,
    max_price            DOUBLE PRECISION NOT NULL,
    n_offers             INTEGER          NOT NULL,
    avg_discount_percent DOUBLE PRECISION,
    loaded_at            TIMESTAMP        NOT NULL,
    PRIMARY KEY (product_key, source, snapshot_date)
);

CREATE TABLE IF NOT EXISTS category_summary (
    category             VARCHAR(100)     NOT NULL,
    snapshot_date        DATE             NOT NULL,
    n_products           INTEGER          NOT NULL,
    n_offers             INTEGER          NOT NULL,
    n_sources            INTEGER          NOT NULL,
    min_price            DOUBLE PRECISION NOT NULL,
    avg_price            DOUBLE PRECISION NOT NULL,
    max_price            DOUBLE PRECISION NOT NULL,
    avg_discount_percent DOUBLE PRECISION,
    promotions           INTEGER          NOT NULL,
    PRIMARY KEY (category, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history (snapshot_date);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
