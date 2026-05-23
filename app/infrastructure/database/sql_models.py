'''
Набор SQL-команд для общения с БД
'''
__all__ = [
    'INSERT_USER', 'INSERT_JOURNAL', 'INSERT_WORKOUT',
    'INSERT_TRAIN', 'INSERT_ROW', 'INSERT_EXERCISE', 'INSERT_ROUTE',
    'GET_USER_BY_TG_ID', 'GET_JOURNAL', 'GET_USER_ID',
    'GET_EXERCISES_BY_ROWS', 'GET_ROUTES_BY_ROWS', 'GET_ROWS_BY_TRAINS',
    'GET_TRAINS_BY_WORKOUT', 'GET_WORKOUT_BY_DATE', 'GET_WORKOUT_BY_ID',
    'UPDATE_JOURNAL_PERIOD', 'UPDATE_JOURNAL_PERIOD_END'
]

################## table creation ###################

SCRIPT_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    last_journal INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    comments TEXT,
    period_start DATE,
    period_end DATE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS update_last_journal
AFTER INSERT ON journals
BEGIN
    UPDATE users
    SET last_journal = NEW.id
    WHERE id = NEW.user_id;
END;

CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_id INTEGER NOT NULL,
    workout_date DATE NOT NULL,
    comments TEXT,
    
    FOREIGN KEY (journal_id)
        REFERENCES journals(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    category TEXT NOT NULL,   -- Climbing/Gym
    type TEXT NOT NULL,       -- Lead/Boulder/GPP/SFP
    comments TEXT,
    
    FOREIGN KEY (workout_id)
        REFERENCES workouts(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    row_order INTEGER NOT NULL,
    comments TEXT,

    FOREIGN KEY (train_id)
        REFERENCES trains(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id INTEGER NOT NULL,
    route_order INTEGER NOT NULL,
    grade TEXT NOT NULL,
    falls INTEGER NOT NULL DEFAULT 0,
    flash BOOLEAN NOT NULL DEFAULT 0,

    FOREIGN KEY (row_id)
        REFERENCES rows(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id INTEGER NOT NULL,
    exercise_order INTEGER NOT NULL,
    name TEXT NOT NULL,
    repeats TEXT NOT NULL,      -- json

    FOREIGN KEY (row_id)
        REFERENCES rows(id)
        ON DELETE CASCADE
);
"""

################ user repo operations ################
################ insert data #########################

INSERT_USER = """
INSERT OR IGNORE INTO users (tg_id, username)
VALUES (?, ?);
"""

INSERT_JOURNAL = """
INSERT INTO journals (user_id, comments, period_start, period_end)
VALUES (?, ?, ?, ?);
"""

INSERT_WORKOUT = """
INSERT INTO workouts (journal_id, workout_date, comments)
VALUES (?, ?, ?);
"""

INSERT_TRAIN = """
INSERT INTO trains (workout_id, category, type, comments)
VALUES (?, ?, ?, ?);
"""

INSERT_ROW = """
INSERT INTO rows (train_id, row_order, comments)
VALUES (?, ?, ?);
"""

INSERT_ROUTE = """
INSERT INTO routes (row_id, route_order, grade, falls, flash)
VALUES (?, ?, ?, ?, ?);
"""

INSERT_EXERCISE = """
INSERT INTO exercises (row_id, exercise_order, name, repeats)
VALUES (?, ?, ?, ?);
"""
################ get data ###########################

GET_USER_BY_TG_ID = """
SELECT *
FROM users
WHERE tg_id = ?;
"""

GET_USER_ID = "SELECT id FROM users WHERE tg_id = ?"

GET_JOURNAL = """
SELECT *
FROM journals
WHERE id = ?;
"""

GET_WORKOUT_BY_ID = """
SELECT *
FROM workouts
WHERE id = ?;
"""

GET_WORKOUT_BY_DATE = """
SELECT *
FROM workouts
WHERE workout_date = ?;
"""

GET_TRAINS_BY_WORKOUT = """
SELECT *
FROM trains
WHERE workout_id = ?;
"""

GET_ROWS_BY_TRAINS = """
SELECT *
FROM rows
WHERE train_id IN ({});
"""

GET_ROUTES_BY_ROWS = """
SELECT *
FROM routes
WHERE row_id IN ({});
"""

GET_EXERCISES_BY_ROWS = """
SELECT *
FROM exercises
WHERE row_id IN ({});
"""

############################## update data #################################

UPDATE_JOURNAL_PERIOD = """
UPDATE journals
SET
    period_start = ?,
    period_end = ?
WHERE id = ?;
"""
UPDATE_JOURNAL_PERIOD_END = """
UPDATE journals
SET
    period_start = ?,
    period_end = ?
WHERE id = ?;
"""