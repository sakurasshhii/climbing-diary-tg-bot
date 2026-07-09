'''
Набор SQL-команд для общения с БД
'''

#—————————————————————— table creation ———————————————————

SCRIPT_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL UNIQUE,
    username TEXT DEFAULT NULL,
    last_journal INTEGER DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT,
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

CREATE_INDICIES = """
CREATE INDEX IF NOT EXISTS idx_journal_user
ON journals(user_id);

CREATE INDEX IF NOT EXISTS idx_workout_journal
ON workouts(journal_id);

CREATE INDEX IF NOT EXISTS idx_train_workout
ON trains(workout_id);

CREATE INDEX IF NOT EXISTS idx_row_train
ON rows(train_id);

CREATE INDEX IF NOT EXISTS idx_route_row
ON routes(row_id);

CREATE INDEX IF NOT EXISTS idx_exercise_row
ON exercises(row_id);
"""

#—————————————————————— user repo operations —————————————
#—————————————————————— insert data ——————————————————————

INSERT_USER = """
INSERT OR IGNORE INTO users (tg_id, username)
VALUES (?, ?);
"""

INSERT_JOURNAL = """
INSERT INTO journals (user_id, name, comments, period_start, period_end)
VALUES (?, ?, ?, ?, ?);
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
#—————————————————————————— get data ——————————————————————————

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

GET_JOURNALS = """
SELECT *
FROM journals
WHERE user_id = ?;
"""

GET_JOURNALS_IDS = """
SELECT *
FROM journals
WHERE id IN ({});"""

GET_WORKOUTS = """
SELECT *
FROM workouts
WHERE journal_id = ?;
"""

GET_WORKOUT = """
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

GET_TRAINS_BY_WORKOUTS = """
SELECT *
FROM trains
WHERE workout_id IN ({});
"""

GET_ROWS_BY_TRAINS = """
SELECT *
FROM rows
WHERE train_id IN ({})
ORDER BY row_index;
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

GET_J_FROM_JOURNALS = """
SELECT * FROM journals
WHERE id=?;"""

GET_J_WORKOUTS = """
SELECT *
FROM workouts
WHERE journal_id=?
ORDER BY workout_date;"""

GET_J_TRAINS = """
SELECT t.*
FROM trains t
JOIN workouts w
    ON w.id=t.workout_id
WHERE w.journal_id=?
ORDER BY t.id;"""

GET_J_ROWS = """
SELECT r.*
FROM rows r
JOIN trains t
    ON t.id = r.train_id
JOIN workouts w
    ON w.id = t.workout_id
WHERE w.journal_id = ?
ORDER BY
    r.train_id,
    r.row_order;
"""

GET_J_ROUTES = """
SELECT
    rt.*
FROM routes rt
JOIN rows r
    ON r.id = rt.row_id
JOIN trains t
    ON t.id = r.train_id
JOIN workouts w
    ON w.id = t.workout_id
WHERE w.journal_id = ?
ORDER BY
    rt.row_id,
    rt.route_order;
"""

GET_J_EXERCISES = """
SELECT
    ex.*
FROM exercises ex
JOIN rows r
    ON r.id = ex.row_id
JOIN trains t
    ON t.id = r.train_id
JOIN workouts w
    ON w.id = t.workout_id
WHERE w.journal_id = ?
ORDER BY
    ex.row_id,
    ex.exercise_order;
"""
#—————————————————————————— update data ——————————————————————————

UPDATE_JOURNAL_PERIOD = """
UPDATE journals
SET
    period_start = ?,
    period_end = ?
WHERE id = ?;
"""

UPDATE_LAST_JOURNAL = """
UPDATE users
SET last_journal = (
    SELECT id
    FROM journals
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT 1
)
WHERE id = ?;
"""
#—————————————————————————— delete data ——————————————————————————

DELETE_JOURNALS = """
DELETE FROM journals
WHERE user_id = ?
AND id IN ({});
"""
