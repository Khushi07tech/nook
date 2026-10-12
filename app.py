from database import init_db, get_db
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, g
import inspect
import json
import os
from services.categorizer import categorize_idea, categorize_entry, chat_msg, ai_quote
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
secret_key = os.environ.get("FLASK_SECRET_KEY")

if not secret_key:
    raise ValueError("No FLASK_SECRET_KEY set in environment variables!")

app.secret_key = secret_key

init_db()
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def parse_sqlite_timestamp(value):
    """Safely converts SQLite datetime into a UTC-aware datetime object."""
    if not value:
        return None
    
    # If it's already a datetime object, no parsing is needed
    if isinstance(value, datetime):
        dt = value
    else:
        # Strip fractional seconds if present
        clean_val = str(value).split('.')[0]
        dt = datetime.strptime(clean_val, "%Y-%m-%d %H:%M:%S")
    
    # Attach UTC timezone if not already present
    if dt.tzinfo is None:  # If datetime is naive
        dt = dt.replace(tzinfo=timezone.utc)  # Assigns UTC timezone
    return dt

@app.template_filter('time_ago')
def time_ago(value):
    """Formats timestamps into relative time strings (e.g., '5m ago')."""
    dt = parse_sqlite_timestamp(value)
    if not dt:
        return ""
    
    now = datetime.now(timezone.utc)  # Prevents timing discrepancies
    seconds = (now - dt).total_seconds()

    # Prevent negative time difference
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
    """Formats timestamps into localized human-readable date strings."""
    dt = parse_sqlite_timestamp(value)
    if not dt:
        return ""
    
    # Convert to local time for human-friendly tooltip display
    local_dt = dt + timedelta(hours=5)
    return local_dt.strftime("%B %d, %Y at %I:%M %p")

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

@app.route("/")
def index():
    """Renders the central landing dashboard."""
    quote = ai_quote() 
    db = get_db()
    not_started_projects = db.execute("SELECT COUNT(*) AS count FROM projects WHERE is_active = 1 AND status = 'not-started'").fetchone()['count']
    active_projects = db.execute("SELECT COUNT(*) AS count FROM projects WHERE is_active = 1 AND status = 'in-progress'").fetchone()['count']
    on_hold_projects = db.execute("SELECT COUNT(*) AS count FROM projects WHERE is_active = 1 AND status = 'on-hold'").fetchone()['count']
    completed_projects = db.execute("SELECT COUNT(*) AS count FROM projects WHERE is_active = 1 AND status = 'completed'").fetchone()['count']
    ideas = db.execute("SELECT COUNT(*) AS count FROM ideas WHERE is_active = 1").fetchone()['count']

    return render_template("index.html", quote=quote, not_started_projects=not_started_projects, active_projects=active_projects, on_hold_projects=on_hold_projects, completed_projects=completed_projects, ideas=ideas)

@app.route("/<string:item_type>/<int:entry_id>/delete", methods=["POST"])
def delete_row(item_type, entry_id):
    """Soft deletes rows from ideas, entries, and project tables upon deactivation."""
    # Whitelist validation: only allow safe table target names
    if item_type not in ["ideas", "entries", "projects"]:
        return "Invalid item type", 400

    db = get_db()
    db.execute(f"UPDATE {item_type} SET is_active = 0 WHERE id = ?", (entry_id,))
    db.commit()

    flash(f"Item successfully deleted from {item_type}.", "success")

    return redirect(request.referrer or url_for("index"))

@app.route("/ideas", methods=["GET", "POST"])
def ideas():
    """Fetching active ideas or parsing and inserting new categorized ideas."""
    if request.method == "GET":
        db = get_db()
        raw_rows = db.execute("SELECT * FROM ideas WHERE is_active = 1 ORDER BY created_at DESC")
        ideas = []

        for raw_row in raw_rows:
            # Converting to dictionary for JSON tag parsing
            idea = dict(raw_row)
            raw_tags = idea.get("ai_tags")
            if raw_tags:
                try:
                    idea["ai_tags"] = json.loads(raw_tags)
                except Exception:
                    idea["ai_tags"] = []
            else:
                idea["ai_tags"] = []

            ideas.append(idea)

        return render_template("ideas.html", ideas=ideas)
    
    else:
        raw_content = request.form.get("raw_content")
        ai_content = categorize_idea(raw_content)
        db = get_db()

        if ai_content:
            ai_category = ai_content["category"]
            ai_tags = ai_content["tags"]
            ai_tags_str = json.dumps(ai_tags)

            db.execute("INSERT INTO ideas (raw_content, ai_category, ai_tags) VALUES (?, ?, ?)", (raw_content, ai_category, ai_tags_str))
            db.commit()
            flash(f"Idea saved and categorized as '{ai_category}'!", "success")
        else:
            # Fallback when AI service returns None
            db.execute("INSERT INTO ideas (raw_content) VALUES (?)", (raw_content,))
            db.commit()
            flash("Idea saved (without categorization)!", "warning")

        return redirect(url_for("ideas"))

@app.route("/projects", methods=["GET", "POST"])
def projects():
    """Fetching active projects or creating new project entries."""
    if request.method == "GET":
        db = get_db()
        projects = db.execute("SELECT * FROM projects WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
        return render_template("projects.html", projects=projects)
    else:
        name = request.form.get("name")
        status = request.form.get("status")
        summary = request.form.get("summary")

        db = get_db()
        db.execute("INSERT INTO projects (name, status, summary) VALUES (?, ?, ?)", (name, status, summary))
        db.commit()

        flash(f"Project saved as '{name}'", "success")
        return redirect(url_for("/projects"))

@app.route("/projects/<int:project_id>/entries", methods=["GET", "POST"])
def project_entries(project_id):
    """Fetching details and entries for a specific project, or adding new project logs."""
    if request.method == "GET":
        db = get_db()
        project = db.execute("SELECT * FROM projects WHERE id = ? AND is_active = 1", (project_id,)).fetchone()
        
        if not project:
            abort(404)

        entries = db.execute("SELECT * FROM entries WHERE project_id = ? AND is_active = 1 ORDER BY entry_type ASC, created_at DESC", (project_id,)).fetchall()
        return render_template("project_detail.html", project=project, entries=entries)
    else:
        raw_content = request.form.get("raw_content")
        ai_content = categorize_entry(raw_content)

        image = request.files.get("image")
        image_path = None

        if image and image.filename != "": 
            filename = secure_filename(image.filename)
            # Generates a unique, random, and collision-safe filename
            filename = f"{uuid.uuid4().hex}_{filename}"

            save_location = os.path.join(UPLOAD_FOLDER, filename)
            image.save(save_location)
            image_path = f"uploads/{filename}"            

        db = get_db()
        if ai_content:
            entry_type = ai_content["entry_type"]
            db.execute("INSERT INTO entries (project_id, raw_content, image_path, entry_type) VALUES (?, ?, ?, ?)", (project_id, raw_content, image_path, entry_type))
            db.commit()
            flash(f"Entry saved and categorized as '{entry_type}'", "success")
        else:
            db.execute("INSERT INTO entries (project_id, raw_content, image_path) VALUES (?, ?, ?)", (project_id, raw_content, image_path))
            db.commit()
            flash("Entry saved (without categorization)", "warning")

        return redirect(url_for("project_entries", project_id=project_id))        

@app.route("/chat", methods=["GET", "POST"])
@app.route("/chat/<int:project_id>", methods=["GET", "POST"])
def chat(project_id=None):
    """Handles general and project-specific chat with the AI companion."""
    db = get_db()

    if project_id:
        project_exists = db.execute("SELECT 1 FROM projects WHERE id = ? AND is_active = 1", (project_id,)).fetchone()
        if not project_exists:
            abort(404)


    if request.method == "GET":
        # Load conversation history for either specific project or global companion
        if project_id:
            msgs = db.execute("SELECT * FROM chat_messages WHERE project_id = ? ORDER BY id ASC LIMIT 30", (project_id,)).fetchall()
        else:
            msgs = db.execute("SELECT * FROM chat_messages WHERE project_id IS NULL ORDER BY id ASC LIMIT 30").fetchall()

        return render_template("companion.html", msgs=msgs, project_id=project_id)
    
    else:
        user_msg = request.form.get("msg", "").strip()
        if not user_msg:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Dynamic context gathering based on scope
        if project_id:
            projects = db.execute("SELECT name, status, summary FROM projects WHERE id = ? AND is_active = 1", (project_id,)).fetchall()
            entries = db.execute("SELECT entry_type, raw_content FROM entries WHERE project_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 15", (project_id,)).fetchall()
            msgs = db.execute("SELECT role, content FROM chat_messages WHERE project_id = ? ORDER BY id DESC LIMIT 10", (project_id,)).fetchall()
        else:
            projects = db.execute("SELECT name, status, summary FROM projects WHERE is_active = 1 ORDER BY id DESC LIMIT 5").fetchall()
            entries = db.execute("SELECT entry_type, raw_content FROM entries WHERE is_active = 1 ORDER BY id DESC LIMIT 15").fetchall()
            msgs = db.execute("SELECT role, content FROM chat_messages WHERE project_id IS NULL ORDER BY id DESC LIMIT 10").fetchall()

        # Format context for AI model prompt
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

        # Store user and assistant messages
        db.execute("INSERT INTO chat_messages (role, content, project_id) VALUES (?, ?, ?)", ("user", user_msg, project_id))
        db.execute("INSERT INTO chat_messages (role, content, project_id) VALUES (?, ?, ?)", ("assistant", ai_msg, project_id))
        db.commit()

        return jsonify({"response": ai_msg})

# Launch Flask development server
if __name__ == "__main__":
    app.run(debug=True)