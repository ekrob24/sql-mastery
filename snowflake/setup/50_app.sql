-- The practice app: Streamlit in Snowflake, from files copied into APP_STAGE by install.sql.
-- It lives in schema SHOP so unqualified table names (customers, orders, ...) resolve to the practice data.
CREATE OR REPLACE STREAMLIT SQL_MASTERY.SHOP.SQL_MASTERY_APP
  FROM '@SQL_MASTERY.APP.APP_STAGE'
  MAIN_FILE = 'streamlit_app.py'
  QUERY_WAREHOUSE = SQL_MASTERY_WH
  TITLE = 'SQL Mastery'
  COMMENT = 'Interactive SQL course: lessons, graded exercises, progress';
