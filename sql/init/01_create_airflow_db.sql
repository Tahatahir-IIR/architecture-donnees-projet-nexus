-- Executed once by the postgres container on first start (docker-entrypoint-initdb.d).
-- The warehouse database (POSTGRES_DB, default ecommerce_db) is created by the image;
-- Airflow needs its own metadata database.
CREATE DATABASE airflow;
