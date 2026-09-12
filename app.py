import json
import os
from services.categorizer import categorize_idea
from database import init_db, db_execute, get_db
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

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
        raw_rows = db_execute("SELECT * FROM ideas ORDER BY created_at DESC")

        rows = []

        for raw_row in raw_rows:
            row_dict = dict(raw_row)

            raw_tags = row_dict.get("ai_tags")
            if raw_tags:
                try:
                    row_dict["ai_tags"] = json.loads(raw_tags)
                except Exception:
                    row_dict["ai_tags"] = []
            else:
                row_dict["ai_tags"] = []


            rows.append(row_dict)


        return render_template("ideas.html", rows=rows)
    
    else:
        raw_content = request.form.get("raw_content")

        ai_content = categorize_idea(raw_content)

        if ai_content:
            ai_category = ai_content["category"]
            ai_tags = ai_content["tags"]
            ai_tags_str = json.dumps(ai_tags)

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ideas (raw_content, ai_category, ai_tags) VALUES (?, ?, ?)", (raw_content, ai_category, ai_tags_str))
            conn.commit()
            conn.close()

            flash(f"Idea saved and categorized as '{ai_category}'!", "success")
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ideas (raw_content) VALUES (?)", (raw_content,))
            conn.commit()
            conn.close()

            flash("Idea saved (without categorization)!", "warning")


        return redirect("/ideas")


# Launch flask developement server
if __name__ == "__main__":
    app.run(debug=True)