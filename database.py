from flask import g
import sqlite3

# Database connection getter
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("nook.db")
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

# Runs schema.sql once
def init_db():
    conn = sqlite3.connect("nook.db")
    file_path = "schema.sql"

    with open (file_path, "r") as file:
        content = file.read()

    # Using 'executescript' so that the whole script can be executed at once
    conn.executescript(content)
    conn.close()