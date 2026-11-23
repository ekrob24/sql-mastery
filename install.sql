-- ============================================================================
-- SQL Mastery — Snowflake installer
-- Paste into a Snowsight SQL worksheet and choose "Run All" (Cmd/Ctrl + Shift + Enter).
-- Then open: Projects » Streamlit » SQL_MASTERY_APP
-- Re-running is safe: it updates lessons and data and never deletes your progress.
-- ============================================================================
USE ROLE ACCOUNTADMIN;

-- 1. The course role (owns everything the course creates). Granted to SYSADMIN, so ACCOUNTADMIN
--    and SYSADMIN users (you) inherit it.
CREATE ROLE IF NOT EXISTS SQL_MASTERY_DEV;
GRANT CREATE DATABASE  ON ACCOUNT TO ROLE SQL_MASTERY_DEV;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE SQL_MASTERY_DEV;
GRANT ROLE SQL_MASTERY_DEV TO ROLE SYSADMIN;

-- 2. Let Snowflake read the course from GitHub.
CREATE DATABASE IF NOT EXISTS SQL_MASTERY_ADMIN COMMENT = 'SQL Mastery installer + build-user policy';
CREATE SCHEMA IF NOT EXISTS SQL_MASTERY_ADMIN.GIT;
CREATE OR REPLACE API INTEGRATION SQL_MASTERY_GIT_API
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/ekrob24/')
  ENABLED = TRUE;
CREATE OR REPLACE GIT REPOSITORY SQL_MASTERY_ADMIN.GIT.SQL_MASTERY_REPO
  API_INTEGRATION = SQL_MASTERY_GIT_API
  ORIGIN = 'https://github.com/ekrob24/sql-mastery.git';
ALTER GIT REPOSITORY SQL_MASTERY_ADMIN.GIT.SQL_MASTERY_REPO FETCH;
GRANT USAGE ON DATABASE SQL_MASTERY_ADMIN TO ROLE SQL_MASTERY_DEV;
GRANT USAGE ON SCHEMA SQL_MASTERY_ADMIN.GIT TO ROLE SQL_MASTERY_DEV;
GRANT READ ON GIT REPOSITORY SQL_MASTERY_ADMIN.GIT.SQL_MASTERY_REPO TO ROLE SQL_MASTERY_DEV;

-- 3. Build data + app as the course role.
USE ROLE SQL_MASTERY_DEV;
CREATE WAREHOUSE IF NOT EXISTS SQL_MASTERY_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;
USE WAREHOUSE SQL_MASTERY_WH;
EXECUTE IMMEDIATE FROM @SQL_MASTERY_ADMIN.GIT.SQL_MASTERY_REPO/branches/main/snowflake/setup/run_all.sql;
COPY FILES INTO @SQL_MASTERY.APP.APP_STAGE FROM @SQL_MASTERY_ADMIN.GIT.SQL_MASTERY_REPO/branches/main/app/;
EXECUTE IMMEDIATE FROM @SQL_MASTERY_ADMIN.GIT.SQL_MASTERY_REPO/branches/main/snowflake/setup/50_app.sql;

-- 4. Spending cap on the course warehouse: notify at 80% of 5 credits/month, suspend at 100%.
USE ROLE ACCOUNTADMIN;
CREATE RESOURCE MONITOR IF NOT EXISTS SQL_MASTERY_RM WITH CREDIT_QUOTA = 5
  TRIGGERS ON 80 PERCENT DO NOTIFY ON 100 PERCENT DO SUSPEND;
ALTER WAREHOUSE SQL_MASTERY_WH SET RESOURCE_MONITOR = SQL_MASTERY_RM;

-- 5. Check: row counts of the practice tables (customers 20, products 25, ... order_items 150, returns 10).
USE ROLE SQL_MASTERY_DEV;
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM SQL_MASTERY.SHOP.customers UNION ALL
SELECT 'products', COUNT(*) FROM SQL_MASTERY.SHOP.products UNION ALL
SELECT 'suppliers', COUNT(*) FROM SQL_MASTERY.SHOP.suppliers UNION ALL
SELECT 'orders', COUNT(*) FROM SQL_MASTERY.SHOP.orders UNION ALL
SELECT 'order_items', COUNT(*) FROM SQL_MASTERY.SHOP.order_items UNION ALL
SELECT 'returns', COUNT(*) FROM SQL_MASTERY.SHOP.returns;
