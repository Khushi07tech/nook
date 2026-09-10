import sqlite3

# Database connection getter
def get_db():
    conn = sqlite3.connect("nook.db")
    conn.row_factory = sqlite3.Row

    return conn


# Handle query management for simple queries
def db_execute(query, params=()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)

    if query.strip().upper().startswith("SELECT"):
        results = cursor.fetchall()
    else:
        results = None
        conn.commit()

    conn.close()
    return results

# Runs schema.sql once
def init_db():
    conn = sqlite3.connect("nook.db")
    file_path = "schema.sql"

    with open (file_path, "r") as file:
        content = file.read()

    # Using 'executescript' so that the whole script can be executed at once
    conn.executescript(content)
    conn.close()