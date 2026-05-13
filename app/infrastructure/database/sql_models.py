'''
Набор SQL-команд для общения с БД
'''

################## table creation ###################

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    username TEXT
);

CREATE TABLE journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    comments TEXT,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_id INTEGER NOT NULL,
    workout_date DATE NOT NULL,
    comments TEXT,
    
    FOREIGN KEY (journal_id)
        REFERENCES journals(id)
        ON DELETE CASCADE
);

CREATE TABLE trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    category TEXT NOT NULL,   -- climb/gym
    type TEXT NOT NULL,       -- Lead/Boulder/GPP/SFP
    comments TEXT,
    
    FOREIGN KEY (workout_id)
        REFERENCES workouts(id)
        ON DELETE CASCADE
);

CREATE TABLE rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    row_order INTEGER NOT NULL,
    comments TEXT,

    FOREIGN KEY (train_id)
        REFERENCES trains(id)
        ON DELETE CASCADE
);

CREATE TABLE routes (
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

CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    repeats TEXT NOT NULL,      -- json

    FOREIGN KEY (row_id)
        REFERENCES rows(id)
        ON DELETE CASCADE
);
"""

################ user repo operatios ################

INSERT_USER = """
INSERT OR IGNORE INTO users (user_id, username)
VALUES (?, ?);
"""

GET_USER_BY_ID = """
SELECT *
FROM users
WHERE user_id = ?;
"""