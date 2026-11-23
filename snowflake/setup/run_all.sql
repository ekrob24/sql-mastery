-- SQL Mastery setup. Runs every step in order (started by install.sql as role SQL_MASTERY_DEV).
-- Safe to re-run: practice data is rebuilt, your progress tables are never dropped.
EXECUTE IMMEDIATE FROM './00_platform.sql';
EXECUTE IMMEDIATE FROM './10_tables.sql';
EXECUTE IMMEDIATE FROM './20_data.sql';
EXECUTE IMMEDIATE FROM './30_app_tables.sql';
