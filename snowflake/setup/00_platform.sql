-- SQL Mastery: warehouse, database and schemas. Runs as role SQL_MASTERY_DEV.
CREATE WAREHOUSE IF NOT EXISTS SQL_MASTERY_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE
  COMMENT = 'SQL Mastery practice';
CREATE DATABASE IF NOT EXISTS SQL_MASTERY COMMENT = 'SQL Mastery: practice warehouse + app';
CREATE SCHEMA IF NOT EXISTS SQL_MASTERY.SHOP COMMENT = 'The e-commerce practice data (rebuilt on every install)';
CREATE SCHEMA IF NOT EXISTS SQL_MASTERY.APP  COMMENT = 'Progress tables and app files (never wiped)';
CREATE STAGE IF NOT EXISTS SQL_MASTERY.APP.APP_STAGE DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'SQL Mastery app files (copied from the GitHub repo by install.sql)';
