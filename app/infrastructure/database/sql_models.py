'''
Набор SQL-команд для общения с БД
'''

################## table creation ###################

CREATE_TABLES = """
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
    category TEXT NOT NULL,   -- climb/gym
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
    name TEXT NOT NULL,
    repeats TEXT NOT NULL,      -- json

    FOREIGN KEY (row_id)
        REFERENCES rows(id)
        ON DELETE CASCADE
);
"""

################ user repo operations ################
################ add data ###########################

INSERT_USER = """
INSERT OR IGNORE INTO users (tg_id, username)
VALUES (?, ?);
"""

INSERT_JOURNAL = """
INSERT INTO journals (user_id, comments)
VALUES (?, ?);
"""

################ get data ###########################

GET_USER_BY_TG_ID = """
SELECT *
FROM users
WHERE tg_id = ?;
"""

GET_USER_ID = "SELECT id FROM users WHERE tg_id = ?"

GET_JOURNAL_BY_ID = """
SELECT *
FROM journals
WHERE user_id = ?;
"""