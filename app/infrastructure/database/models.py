INIT_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE
)
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    username TEXT
);
"""

INSERT_USER = """
INSERT OR IGNORE INTO users (user_id, username)
VALUES (?, ?);
"""

GET_USER_BY_ID = """
SELECT id, user_id, username
FROM users
WHERE user_id = ?;
"""