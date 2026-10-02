import inspect
import json
import os
import uuid
from werkzeug.utils import secure_filename
from services.categorizer import categorize_idea, categorize_entry, chat_msg
from database import init_db, db_execute, get_db
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

init_db()
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    # Convert to local time for human-friendly tooltip display 

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

@app.route("/projects", methods=["GET", "POST"])
def projects():
    if request.method == "GET":
        rows = db_execute("SELECT * FROM projects ORDER BY created_at DESC")
        return render_template("projects.html", rows=rows)
    else:
        name = request.form.get("name")
        status = request.form.get("status")
        summary = request.form.get("summary")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects (name, status, summary) VALUES (?, ?, ?)", (name, status, summary))
        conn.commit()
        conn.close()

        flash(f"Project saved as '{name}'", "success")

        return redirect("/projects")

@app.route("/projects/<int:project_id>/entries", methods=["GET", "POST"])
def project_entries(project_id):
    if request.method == "GET":
        project = db_execute("SELECT * FROM projects WHERE id = ?", (project_id,))[0]
        entries = db_execute("SELECT * FROM entries WHERE project_id = (?) ORDER BY entry_type ASC, created_at DESC", (project_id,))
        return render_template("project_detail.html", project=project, entries=entries)
    else:
        raw_content = request.form.get("raw_content")
        ai_content = categorize_entry(raw_content)

        image = request.files.get("image")

        image_path = None

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            filename = f"{uuid.uuid4().hex}_{filename}"

            save_location = os.path.join(UPLOAD_FOLDER, filename)
            image.save(save_location)

            image_path = f"uploads/{filename}"            

        if ai_content:
            entry_type = ai_content["entry_type"]
            db_execute("INSERT INTO entries (project_id, raw_content, image_path, entry_type) VALUES (?, ?, ?, ?)", (project_id, raw_content, image_path, entry_type))

            flash(f"Entry saved and categorized as '{entry_type}'", "success")

            return redirect(f"/projects/{project_id}/entries")
        else:
            db_execute("INSERT INTO entries (project_id, raw_content, image_path) VALUES (?, ?, ?)", (project_id, raw_content, image_path))

            flash("Entry saved (without categorization)", "warning")
            return redirect(f"/projects/{project_id}/entries")

@app.route("/chat", methods=["GET", "POST"])
@app.route("/chat/<int:project_id>", methods=["GET", "POST"])
def chat(project_id=None):
    if request.method == "POST":
        user_msg = request.form.get("msg", "").strip()
        if not user_msg:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Dynamic context gathering based on scope
        if project_id:
            projects = db_execute("SELECT name, status, summary FROM projects WHERE id = ?", (project_id,))
            entries = db_execute("SELECT entry_type, raw_content FROM entries WHERE project_id = ? ORDER BY id DESC LIMIT 15", (project_id,))
            msgs = db_execute("SELECT role, content FROM chat_messages WHERE project_id = ? ORDER BY id DESC LIMIT 10", (project_id,))
        else:
            projects = db_execute("SELECT name, status FROM projects ORDER BY id DESC LIMIT 5")
            entries = db_execute("SELECT entry_type, raw_content FROM entries ORDER BY id DESC LIMIT 15")
            msgs = db_execute("SELECT role, content FROM chat_messages WHERE project_id IS NULL ORDER BY id DESC LIMIT 10")

        # Format context
        entry_formatted = "\n".join([f"- [{row['entry_type']}] {row['raw_content']}" for row in entries]) if entries else "None"
        project_formatted = "\n".join([f"- {row['name']} ({row['status']}): {row['summary']}" for row in projects]) if projects else "None"
        msgs_formatted = "\n".join([f"{row['role'].capitalize()}: {row['content']}" for row in reversed(msgs)]) if msgs else "None"

        context = inspect.cleandoc(f"""
            === PROJECTS ===
            {project_formatted}

            === RECENT ENTRIES ===
            {entry_formatted}

            === CONVERSATION HISTORY ===
            {msgs_formatted}

            === CURRENT MESSAGE ===
            {user_msg}
        """)

        ai_msg = chat_msg(context)

        # Store message with or without project_id
        db_execute("INSERT INTO chat_messages (role, content, project_id) VALUES (?, ?, ?)", ("user", user_msg, project_id))
        db_execute("INSERT INTO chat_messages (role, content, project_id) VALUES (?, ?, ?)", ("assistant", ai_msg, project_id))

        return jsonify({"response": ai_msg})

    else:
        # GET request: load history for either project or global companion
        if project_id:
            msgs = db_execute("SELECT * FROM chat_messages WHERE project_id = ? ORDER BY id ASC LIMIT 30", (project_id,))
        else:
            msgs = db_execute("SELECT * FROM chat_messages WHERE project_id IS NULL ORDER BY id ASC LIMIT 30")

        return render_template("companion.html", msgs=msgs, project_id=project_id)
            
# Launch flask developement server
if __name__ == "__main__":
    app.run(debug=True)




