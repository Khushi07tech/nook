from database import init_db, db_execute, get_db
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

init_db()

def parse_sqlite_timestamp(value):
    """Safely converts SQLite datetime into a UTC-aware datetime object."""
    if not value:
        return None
    # if its already a datetime object, no parsing is needed
    if isinstance(value, datetime):
        dt = value
    else:
        # Strip fractional seconds if present
        clean_val = str(value).split('.')[0]
        dt = datetime.strptime(clean_val, "%Y-%m-%d %H:%M:%S")
    
    # Attach UTC timezone if not already present
    if dt.tzinfo is None: # If datetime is naive
        dt = dt.replace(tzinfo=timezone.utc) # Slaps a UTC label
    return dt

@app.template_filter('time_ago')
def time_ago(value):
    dt = parse_sqlite_timestamp(value)
    if not dt:
        return ""
    
    now = datetime.now(timezone.utc) # Prevents timing discrepancies
    seconds = (now - dt).total_seconds()

    # Prevents negative time difference
    if seconds < 0:
        seconds = 0

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    elif seconds < 604800:
        return f"{int(seconds // 86400)}d ago"
    else:
        return dt.strftime("%b %d")

@app.template_filter('full_date')
def full_date(value):
    dt = parse_sqlite_timestamp(value)
    if not dt:
        return ""
    # Convert to local time for human-friendly tooltip display if desired

    local_dt = dt + timedelta(hours=5)

    return local_dt.strftime("%B %d, %Y at %I:%M %p")

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ideas", methods=["GET", "POST"])
def ideas():
    if request.method == "GET":
        rows = db_execute("SELECT * FROM ideas")
        return render_template("ideas.html", rows=rows)
    else:
        raw_content = request.form.get("raw_content")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ideas (raw_content) VALUES (?)", (raw_content,))
        conn.commit()
        conn.close()
        return redirect("/ideas")


# Launch flask developement server
if __name__ == "__main__":
    app.run(debug=True)