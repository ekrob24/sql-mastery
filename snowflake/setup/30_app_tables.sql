-- Progress storage. CREATE IF NOT EXISTS: reinstalling never erases your progress.
CREATE TABLE IF NOT EXISTS SQL_MASTERY.APP.PROGRESS (
    exercise_key     VARCHAR PRIMARY KEY,   -- e.g. '10.3'
    status           VARCHAR,               -- attempted | needs_explanation | completed
    attempts         INTEGER DEFAULT 0,
    hints_revealed   INTEGER DEFAULT 0,
    solution_viewed  BOOLEAN DEFAULT FALSE,
    explanation      VARCHAR,
    last_sql         VARCHAR,
    first_attempt_at TIMESTAMP_NTZ,
    completed_at     TIMESTAMP_NTZ,
    updated_at       TIMESTAMP_NTZ
);
CREATE TABLE IF NOT EXISTS SQL_MASTERY.APP.SUBMISSIONS (
    submitted_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    exercise_key  VARCHAR,
    passed        BOOLEAN,
    plan_ok       BOOLEAN,
    message       VARCHAR,
    sql_text      VARCHAR
);
CREATE TABLE IF NOT EXISTS SQL_MASTERY.APP.CHECKPOINTS (
    checkpoint    VARCHAR PRIMARY KEY,      -- 'joins'
    passed        BOOLEAN,
    attempts      INTEGER,
    passed_at     TIMESTAMP_NTZ,
    last_results  VARIANT
);
