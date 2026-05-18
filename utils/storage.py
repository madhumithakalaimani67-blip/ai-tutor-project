import sqlite3
import json
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "eduai.db")

def init_db():
    if not os.path.exists("database"):
        os.makedirs("database")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Pending Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_users (
        email TEXT PRIMARY KEY,
        password TEXT,
        otp_code TEXT,
        expires_at TIMESTAMP
    )
    """)
    
    # 3. User Profile
    _ensure_table(cursor, "user_profile", """
    CREATE TABLE user_profile (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        age TEXT,
        interests TEXT,
        learning_style TEXT,
        daily_time TEXT,
        primary_goal TEXT,
        status TEXT,
        pace TEXT,
        skill_level TEXT,
        challenges TEXT,
        known_topics TEXT,
        target_deadline TEXT,
        learning_reason TEXT,
        target_certification TEXT,
        preferred_language TEXT,
        study_device TEXT,
        college_company TEXT,
        reminder_time TEXT DEFAULT '20:00',
        theme TEXT DEFAULT 'Glass (Purple)',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """, required_columns=["user_id", "name", "theme", "primary_goal"])
    
    # Add new optional columns if they don't exist
    for col in ["known_topics", "target_deadline", "learning_reason", "target_certification", "preferred_language", "study_device", "college_company", "reminder_time", "status", "pace", "skill_level", "challenges"]:
        try:
            cursor.execute(f"ALTER TABLE user_profile ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists

    # 4. Sessions - task_id links session to a checklist goal
    _ensure_table(cursor, "sessions", """
    CREATE TABLE sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_id INTEGER,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        planned_duration INTEGER,
        actual_duration INTEGER,
        focus_score INTEGER,
        distraction_count INTEGER DEFAULT 0,
        drowsy_count INTEGER DEFAULT 0,
        phone_count INTEGER DEFAULT 0,
        zone_out_count INTEGER DEFAULT 0,
        pause_count INTEGER DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )
    """, required_columns=["user_id", "task_id", "distraction_count", "drowsy_count", "phone_count", "zone_out_count", "pause_count"])

    # 5. Roadmaps
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roadmaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        goal TEXT,
        duration TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 6. Tasks (Checklist Items)
    _ensure_table(cursor, "tasks", """
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        roadmap_id INTEGER,
        description TEXT,
        status TEXT DEFAULT 'pending', 
        week INTEGER,
        day INTEGER,
        order_num INTEGER,
        breakdown TEXT, -- JSON string of sub-tasks
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (roadmap_id) REFERENCES roadmaps (id)
    )
    """, required_columns=["user_id", "breakdown", "day"])

    # 7. Notes (Knowledge Vault)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_id INTEGER,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )
    """)

    # 8. Doubt Chats Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doubt_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        messages TEXT, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # 9. Daily Logins
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_logins (
        user_id INTEGER,
        login_date DATE,
        PRIMARY KEY(user_id, login_date),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    conn.commit()
    conn.close()

def _ensure_table(cursor, table_name, create_sql, required_columns):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [row[1] for row in cursor.fetchall()]
        if not existing_cols:
            cursor.execute(create_sql)
        else:
            missing = [c for c in required_columns if c not in existing_cols]
            if missing:
                for col in missing:
                    try:
                        col_type = "INTEGER DEFAULT 0" if "count" in col or col in ["week", "day", "order_num"] else "TEXT"
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type}")
                    except sqlite3.OperationalError:
                        pass
    except Exception:
        cursor.execute(create_sql)

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, password):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hash_password(password)))
        conn.commit(); user_id = cursor.lastrowid; conn.close(); return user_id
    except sqlite3.IntegrityError: conn.close(); return None

def verify_user(email, password):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ? AND password = ?", (email, hash_password(password)))
    row = cursor.fetchone(); conn.close(); return row[0] if row else None

def email_exists(email):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone(); conn.close(); return True if row else False

def reset_password(email, new_password):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hash_password(new_password), email))
    conn.commit(); conn.close(); return True

def save_pending_user(email, password, otp_code):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO pending_users (email, password, otp_code, expires_at) VALUES (?, ?, ?, datetime('now', '+10 minutes'))", (email, hash_password(password), otp_code))
    conn.commit(); conn.close()

def verify_otp(email, code):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT password FROM pending_users WHERE email = ? AND otp_code = ? AND expires_at > datetime('now')", (email, code))
    row = cursor.fetchone()
    if row:
        pwd = row[0]
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, pwd))
            uid = cursor.lastrowid; cursor.execute("DELETE FROM pending_users WHERE email = ?", (email,))
            conn.commit(); conn.close(); return uid
        except: pass
    conn.close(); return None

def save_profile(user_id, data):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO user_profile (
            user_id, name, email, age, interests, learning_style, daily_time, primary_goal, theme,
            known_topics, target_deadline, learning_reason, target_certification, preferred_language, study_device, college_company, reminder_time,
            status, pace, skill_level, challenges
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id, data.get("name"), data.get("email"), data.get("age"), data.get("interests"), 
        data.get("learning_style"), data.get("daily_time"), data.get("primary_goal"), data.get("theme", "Glass (Purple)"),
        data.get("known_topics", ""), data.get("target_deadline", ""), data.get("learning_reason", ""),
        data.get("target_certification", ""), data.get("preferred_language", ""), data.get("study_device", ""),
        data.get("college_company", ""), data.get("reminder_time", "20:00"),
        data.get("status", ""), data.get("pace", ""), data.get("skill_level", ""), data.get("challenges", "")
    ))
    conn.commit(); conn.close()

def get_profile(user_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    try: cursor.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
    except: conn.close(); init_db(); return None
    row = cursor.fetchone(); conn.close(); return dict(row) if row else None

def get_all_profiles():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    try: cursor.execute("SELECT * FROM user_profile")
    except: conn.close(); return []
    rows = cursor.fetchall(); conn.close(); return [dict(r) for r in rows]

def update_theme(user_id, theme_name):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE user_profile SET theme = ? WHERE user_id = ?", (theme_name, user_id))
    conn.commit(); conn.close()

def save_session(user_id, data):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (
            user_id, task_id, start_time, end_time, planned_duration, 
            actual_duration, focus_score, distraction_count, pause_count, 
            notes, drowsy_count, phone_count, zone_out_count
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id, data.get("task_id"), data.get("start_time"), data.get("end_time"), 
        data.get("planned_duration"), data.get("actual_duration"), data.get("focus_score"), 
        data.get("distraction_count", 0), data.get("pause_count", 0), data.get("notes"),
        data.get("drowsy_count", 0), data.get("phone_count", 0), data.get("zone_out_count", 0)
    ))
    conn.commit(); conn.close()

def get_sessions(user_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY end_time DESC LIMIT 200", (user_id,))
    rows = cursor.fetchall(); conn.close(); return [dict(r) for r in rows]

def get_sessions_by_roadmap(user_id, roadmap_id):
    """Return all sessions whose task belongs to the given roadmap."""
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("""
        SELECT s.* FROM sessions s
        JOIN tasks t ON s.task_id = t.id
        WHERE s.user_id = ? AND t.roadmap_id = ?
        ORDER BY s.end_time DESC
    """, (user_id, roadmap_id))
    rows = cursor.fetchall(); conn.close(); return [dict(r) for r in rows]

def delete_session(sid):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (sid,))
    conn.commit(); conn.close()

def fix_task_day_numbering(user_id):
    """
    One-time migration: converts global day numbers to week-relative day numbers.
    E.g. Week 2 days 8-14 become 1-7.
    """
    from collections import defaultdict
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute(
        "SELECT id, week, day FROM tasks WHERE user_id = ? ORDER BY week, day",
        (user_id,)
    )
    rows = cursor.fetchall()
    # Find the minimum day value per week
    week_min = defaultdict(lambda: 999)
    for _, week, day in rows:
        if day < week_min[week]:
            week_min[week] = day
    # Renumber: new_day = old_day - week_min[week] + 1
    for task_id, week, day in rows:
        new_day = day - week_min[week] + 1
        if new_day != day:
            cursor.execute("UPDATE tasks SET day = ? WHERE id = ?", (new_day, task_id))
    conn.commit(); conn.close()


def record_login(user_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM daily_logins WHERE user_id = ?", (user_id,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO daily_logins (user_id, login_date) SELECT DISTINCT user_id, date(start_time) FROM sessions WHERE user_id = ?", (user_id,))
    cursor.execute("INSERT OR IGNORE INTO daily_logins (user_id, login_date) VALUES (?, ?)", (user_id, today_str))
    conn.commit(); conn.close()

def get_streak(user_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT login_date FROM daily_logins WHERE user_id = ? ORDER BY login_date DESC", (user_id,))
    rows = cursor.fetchall(); conn.close()
    if not rows: return 0
    from datetime import datetime
    streak = 0
    today = datetime.now().date()
    try:
        last_login = datetime.strptime(rows[0][0], "%Y-%m-%d").date()
        if (today - last_login).days > 1: return 0
        streak = 1
        for i in range(1, len(rows)):
            prev = datetime.strptime(rows[i-1][0], "%Y-%m-%d").date()
            curr = datetime.strptime(rows[i][0], "%Y-%m-%d").date()
            if (prev - curr).days == 1: streak += 1
            else: break
    except: return 0
    return streak

def get_login_history(user_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT login_date FROM daily_logins WHERE user_id = ? ORDER BY login_date ASC", (user_id,))
    rows = cursor.fetchall(); conn.close()
    return [row[0] for row in rows]

def save_roadmap(user_id, goal, duration, content):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO roadmaps (user_id, goal, duration, content) VALUES (?, ?, ?, ?)", (user_id, goal, duration, content))
    rid = cursor.lastrowid; conn.commit(); conn.close()
    return rid

def update_roadmap(roadmap_id, goal, duration, content):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE roadmaps SET goal = ?, duration = ?, content = ? WHERE id = ?", (goal, duration, content, roadmap_id))
    conn.commit(); conn.close()

def get_latest_roadmap(user_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    row = cursor.fetchone(); conn.close(); return dict(row) if row else None

def get_all_roadmaps(user_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall(); conn.close(); return [dict(r) for r in rows]

def get_roadmap_by_id(user_id, roadmap_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM roadmaps WHERE user_id = ? AND id = ?", (user_id, roadmap_id))
    row = cursor.fetchone(); conn.close(); return dict(row) if row else None

def delete_roadmap(roadmap_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE roadmap_id = ?", (roadmap_id,))
    task_ids = [row[0] for row in cursor.fetchall()]
    for tid in task_ids:
        cursor.execute("UPDATE sessions SET task_id = NULL WHERE task_id = ?", (tid,))
        cursor.execute("DELETE FROM notes WHERE task_id = ?", (tid,))
    cursor.execute("DELETE FROM tasks WHERE roadmap_id = ?", (roadmap_id,))
    cursor.execute("DELETE FROM roadmaps WHERE id = ?", (roadmap_id,))
    conn.commit(); conn.close()

def save_tasks(user_id, roadmap_id, task_list):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    for t in task_list:
        breakdown_json = json.dumps(t.get('vault_breakdown', t.get('subtasks', [])))
        cursor.execute("""
            INSERT INTO tasks (user_id, roadmap_id, description, week, day, order_num, breakdown) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, roadmap_id, t.get('desc', t.get('task')), 
            t.get('week', 1), t.get('day', 1), t.get('order', 0), 
            breakdown_json
        ))
    conn.commit(); conn.close()

def clear_roadmap_tasks(roadmap_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE roadmap_id = ?", (roadmap_id,))
    conn.commit(); conn.close()

def get_tasks(user_id, roadmap_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ? AND roadmap_id = ? ORDER BY week, order_num", (user_id, roadmap_id))
    rows = cursor.fetchall(); conn.close(); return [dict(r) for r in rows]

def update_task_status(task_id, status):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit(); conn.close()

def add_note(user_id, task_id, content):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (user_id, task_id, content) VALUES (?, ?, ?)", (user_id, task_id, content))
    conn.commit(); conn.close()

def get_notes(user_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall(); conn.close(); return [dict(r) for r in rows]

def create_doubt_chat(user_id, title="New Chat"):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO doubt_chats (user_id, title, messages) VALUES (?, ?, ?)", (user_id, title, json.dumps([])))
    chat_id = cursor.lastrowid; conn.commit(); conn.close(); return chat_id

def update_doubt_chat(chat_id, messages):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE doubt_chats SET messages = ? WHERE id = ?", (json.dumps(messages), chat_id))
    conn.commit(); conn.close()

def update_chat_title(chat_id, title):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE doubt_chats SET title = ? WHERE id = ?", (title, chat_id))
    conn.commit(); conn.close()

def get_user_doubt_chats(user_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at FROM doubt_chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall(); conn.close(); return [dict(r) for r in rows]

def get_doubt_chat_by_id(chat_id):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM doubt_chats WHERE id = ?", (chat_id,))
    row = cursor.fetchone(); conn.close(); return dict(row) if row else None

def delete_doubt_chat(chat_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM doubt_chats WHERE id = ?", (chat_id,))
    conn.commit(); conn.close()

def full_reset(user_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    tables = ["user_profile", "roadmaps", "tasks", "doubt_chats", "sessions", "notes"]
    for table in tables:
        cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
    conn.commit(); conn.close()

init_db()
