import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, g, abort
)

APP_NAME = "Campus Pulse"
DB_FILENAME = "campus_pulse.db"

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("CAMPUS_PULSE_SECRET", "dev-secret-change-me")
    app.config["ADMIN_PASSWORD"] = os.environ.get("CAMPUS_PULSE_ADMIN_PASSWORD", "admin")
    app.config["DATABASE"] = os.path.join(app.instance_path, DB_FILENAME)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    @app.before_request
    def _ensure_db():
        init_db()

    def get_db():
        if "db" not in g:
            conn = sqlite3.connect(app.config["DATABASE"])
            conn.row_factory = sqlite3.Row
            g.db = conn
        return g.db

    @app.teardown_appcontext
    def close_db(exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db_path = app.config["DATABASE"]
        if os.path.exists(db_path):
            return
        db = sqlite3.connect(db_path)
        db.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                display_name TEXT,
                anonymous INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'open',
                lecturer_note TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
            );

            INSERT OR IGNORE INTO courses (code, name, created_at)
            VALUES ('CS101', 'Demo Course: CS101', datetime('now'));
            """
        )
        db.commit()
        db.close()

    def require_lecturer(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("is_lecturer"):
                return redirect(url_for("lecturer_login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def require_course(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("course_id"):
                flash("Please join a course first.", "warning")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped

    def now_iso():
        return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    @app.route("/", methods=["GET"])
    def index():
        db = get_db()
        courses = db.execute("SELECT id, code, name FROM courses ORDER BY created_at DESC").fetchall()
        return render_template("index.html", app_name=APP_NAME, courses=courses)

    @app.route("/about", methods=["GET"])
    def about():
        return render_template("about.html", app_name=APP_NAME)

    @app.route("/student/join", methods=["POST"])
    def student_join():
        course_code = (request.form.get("course_code") or "").strip().upper()
        display_name = (request.form.get("display_name") or "").strip()
        anonymous = 1 if request.form.get("anonymous") == "on" else 0

        if not course_code:
            flash("Course code is required.", "danger")
            return redirect(url_for("index"))

        db = get_db()
        course = db.execute("SELECT id, code, name FROM courses WHERE code = ?", (course_code,)).fetchone()
        if course is None:
            flash(f"Course '{course_code}' not found. Ask your lecturer to create it.", "warning")
            return redirect(url_for("index"))

        session["course_id"] = int(course["id"])
        session["course_code"] = course["code"]
        session["course_name"] = course["name"]
        session["student_display_name"] = display_name
        session["student_anonymous"] = anonymous

        flash(f"Joined {course['code']} — {course['name']}.", "success")
        return redirect(url_for("student_room"))

    @app.route("/student", methods=["GET"])
    @require_course
    def student_room():
        course_id = int(session["course_id"])
        course_code = session.get("course_code", "")
        course_name = session.get("course_name", "")
        display_name = session.get("student_display_name", "")
        anonymous = int(session.get("student_anonymous", 1))

        return render_template(
            "student.html",
            app_name=APP_NAME,
            course_id=course_id,
            course_code=course_code,
            course_name=course_name,
            display_name=display_name,
            anonymous=anonymous
        )

    @app.route("/student/comment", methods=["POST"])
    @require_course
    def student_comment():
        content = (request.form.get("content") or "").strip()
        if not content:
            flash("Comment cannot be empty.", "danger")
            return redirect(url_for("student_room"))

        course_id = int(session["course_id"])
        display_name = (session.get("student_display_name") or "").strip()
        anonymous = int(session.get("student_anonymous", 1))

        db = get_db()
        db.execute(
            """
            INSERT INTO comments (course_id, content, display_name, anonymous, status, created_at)
            VALUES (?, ?, ?, ?, 'open', ?)
            """,
            (course_id, content, display_name if display_name else None, anonymous, now_iso())
        )
        db.commit()

        flash("Submitted! Your comment is now visible to the lecturer.", "success")
        return redirect(url_for("student_room"))

    @app.route("/student/leave", methods=["POST"])
    def student_leave():
        for k in ["course_id", "course_code", "course_name", "student_display_name", "student_anonymous"]:
            session.pop(k, None)
        flash("You left the course.", "info")
        return redirect(url_for("index"))

    # --- Lecturer ---
    @app.route("/lecturer/login", methods=["GET", "POST"])
    def lecturer_login():
        if request.method == "POST":
            password = request.form.get("password") or ""
            if password == app.config["ADMIN_PASSWORD"]:
                session["is_lecturer"] = True
                flash("Logged in as lecturer.", "success")
                nxt = request.args.get("next") or url_for("lecturer_dashboard")
                return redirect(nxt)
            flash("Wrong password.", "danger")

        return render_template("lecturer_login.html", app_name=APP_NAME)

    @app.route("/lecturer/logout", methods=["POST"])
    def lecturer_logout():
        session.pop("is_lecturer", None)
        flash("Logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/lecturer", methods=["GET"])
    @require_lecturer
    def lecturer_dashboard():
        db = get_db()
        courses = db.execute("SELECT id, code, name, created_at FROM courses ORDER BY created_at DESC").fetchall()
        return render_template("lecturer_dashboard.html", app_name=APP_NAME, courses=courses)

    @app.route("/lecturer/course/create", methods=["POST"])
    @require_lecturer
    def lecturer_create_course():
        code = (request.form.get("code") or "").strip().upper()
        name = (request.form.get("name") or "").strip()

        if not code or not name:
            flash("Both course code and course name are required.", "danger")
            return redirect(url_for("lecturer_dashboard"))

        db = get_db()
        try:
            db.execute(
                "INSERT INTO courses (code, name, created_at) VALUES (?, ?, ?)",
                (code, name, now_iso())
            )
            db.commit()
            flash(f"Course {code} created.", "success")
        except sqlite3.IntegrityError:
            flash(f"Course code '{code}' already exists.", "warning")

        return redirect(url_for("lecturer_dashboard"))

    @app.route("/lecturer/course/<int:course_id>", methods=["GET"])
    @require_lecturer
    def lecturer_course(course_id: int):
        db = get_db()
        course = db.execute("SELECT id, code, name FROM courses WHERE id = ?", (course_id,)).fetchone()
        if course is None:
            abort(404)

        status = request.args.get("status", "open").strip().lower()
        if status not in ("open", "resolved", "all"):
            status = "open"

        if status == "all":
            comments = db.execute(
                """
                SELECT * FROM comments
                WHERE course_id = ?
                ORDER BY created_at DESC
                """,
                (course_id,)
            ).fetchall()
        else:
            comments = db.execute(
                """
                SELECT * FROM comments
                WHERE course_id = ? AND status = ?
                ORDER BY created_at DESC
                """,
                (course_id, status)
            ).fetchall()

        return render_template(
            "lecturer_course.html",
            app_name=APP_NAME,
            course=course,
            comments=comments,
            status=status
        )

    @app.route("/lecturer/comment/<int:comment_id>/resolve", methods=["POST"])
    @require_lecturer
    def lecturer_resolve_comment(comment_id: int):
        note = (request.form.get("lecturer_note") or "").strip()
        db = get_db()
        db.execute(
            """
            UPDATE comments
            SET status = 'resolved',
                lecturer_note = ?,
                resolved_at = ?
            WHERE id = ?
            """,
            (note if note else None, now_iso(), comment_id)
        )
        db.commit()
        flash("Marked as resolved.", "success")

        course_id = request.form.get("course_id")
        if course_id:
            return redirect(url_for("lecturer_course", course_id=int(course_id), status=request.args.get("status", "open")))
        return redirect(url_for("lecturer_dashboard"))

    @app.route("/lecturer/comment/<int:comment_id>/reopen", methods=["POST"])
    @require_lecturer
    def lecturer_reopen_comment(comment_id: int):
        db = get_db()
        db.execute(
            """
            UPDATE comments
            SET status = 'open',
                resolved_at = NULL
            WHERE id = ?
            """,
            (comment_id,)
        )
        db.commit()
        flash("Re-opened.", "info")
        course_id = request.form.get("course_id")
        if course_id:
            return redirect(url_for("lecturer_course", course_id=int(course_id), status=request.args.get("status", "open")))
        return redirect(url_for("lecturer_dashboard"))

    # --- API (polling for "real-time") ---
    @app.route("/api/comments/<int:course_id>", methods=["GET"])
    def api_comments(course_id: int):
        db = get_db()
        rows = db.execute(
            """
            SELECT c.id, c.content, c.display_name, c.anonymous, c.status,
                   c.lecturer_note, c.created_at, c.resolved_at
            FROM comments c
            WHERE c.course_id = ?
            ORDER BY c.created_at DESC
            LIMIT 100
            """,
            (course_id,)
        ).fetchall()

        def format_name(r):
            if int(r["anonymous"]) == 1:
                return "Anonymous"
            if r["display_name"]:
                return r["display_name"]
            return "Student"

        data = []
        for r in rows:
            data.append({
                "id": int(r["id"]),
                "content": r["content"],
                "name": format_name(r),
                "status": r["status"],
                "lecturer_note": r["lecturer_note"],
                "created_at": r["created_at"],
                "resolved_at": r["resolved_at"],
            })
        return jsonify({"course_id": course_id, "comments": data})

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "app": APP_NAME})

    return app


app = create_app()

if __name__ == "__main__":
    # For local development only
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)
