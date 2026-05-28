from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import pymysql
import time

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hangeul5-todo-secret-key")
CORS(app)

SQLITE_DB = "todo.db"

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "1234"),
    "database": os.environ.get("MYSQL_DATABASE", "todo_log_db"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "charset": "utf8mb4",
    "connect_timeout": int(os.environ.get("MYSQL_CONNECT_TIMEOUT", "1")),
    "read_timeout": int(os.environ.get("MYSQL_READ_TIMEOUT", "1")),
    "write_timeout": int(os.environ.get("MYSQL_WRITE_TIMEOUT", "1")),
}
MYSQL_LOG_ENABLED = os.environ.get("MYSQL_LOG_ENABLED", "1").strip().lower() not in {
    "0", "false", "no", "off"
}
MYSQL_LOG_RETRY_SECONDS = int(os.environ.get("MYSQL_LOG_RETRY_SECONDS", "30"))
_mysql_log_available = False
_mysql_log_retry_at = 0.0


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_sqlite_connection():
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite_db():
    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS member (
            idx INTEGER PRIMARY KEY AUTOINCREMENT,
            uname TEXT NOT NULL,
            uid TEXT NOT NULL UNIQUE,
            upwd TEXT NOT NULL,
            datetime TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS todolist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            uid TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            datetime TEXT NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) AS cnt FROM member WHERE uid = ?", ("test",))
    if cur.fetchone()["cnt"] == 0:
        cur.execute(
            "INSERT INTO member (uname, uid, upwd, datetime) VALUES (?, ?, ?, ?)",
            ("테스트유저", "test", "1234", now_str())
        )
    conn.commit()
    conn.close()


def get_mysql_connection_without_db():
    config = MYSQL_CONFIG.copy()
    config.pop("database", None)
    return pymysql.connect(**config)


def get_mysql_connection():
    return pymysql.connect(**MYSQL_CONFIG)


def init_mysql_log_db():
    """MySQL 서버가 있으면 로그 DB와 테이블을 자동 생성"""
    global _mysql_log_available, _mysql_log_retry_at

    if not MYSQL_LOG_ENABLED:
        _mysql_log_available = False
        print("[MySQL query logging disabled]")
        return

    try:
        db_name = MYSQL_CONFIG["database"]
        conn = get_mysql_connection_without_db()
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET utf8mb4")
        conn.commit()
        cur.close()
        conn.close()

        conn = get_mysql_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type VARCHAR(20) NOT NULL,
                sql_text TEXT NOT NULL,
                datetime DATETIME NOT NULL
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        _mysql_log_available = True
        _mysql_log_retry_at = 0.0
        print("[MySQL 로그 DB 준비 완료]")
    except Exception as e:
        _mysql_log_available = False
        _mysql_log_retry_at = time.monotonic() + MYSQL_LOG_RETRY_SECONDS
        print("[MySQL 로그 DB 연결 실패]", e)


def log_query(sql, params=None):
    """모든 주요 SQLite 쿼리를 MySQL에 기록"""
    global _mysql_log_available, _mysql_log_retry_at

    if not MYSQL_LOG_ENABLED:
        return

    if not _mysql_log_available:
        if time.monotonic() < _mysql_log_retry_at:
            return
        init_mysql_log_db()
        if not _mysql_log_available:
            return

    try:
        query_type = sql.strip().split()[0].lower()
        full_sql = sql.strip()
        if params:
            full_sql += f" | params={params}"

        conn = get_mysql_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO query_log (type, sql_text, datetime) VALUES (%s, %s, %s)",
            (query_type, full_sql, now_str())
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        _mysql_log_available = False
        _mysql_log_retry_at = time.monotonic() + MYSQL_LOG_RETRY_SECONDS
        # MySQL 문제가 있어도 SQLite CRUD 기능은 중단하지 않음
        print("[쿼리 로그 저장 실패]", e)


def login_required():
    return "uid" in session


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/me", methods=["GET"])
def me():
    if login_required():
        return jsonify({"logged_in": True, "uid": session["uid"], "uname": session.get("uname")})
    return jsonify({"logged_in": False})


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    uname = data.get("uname", "").strip()
    uid = data.get("uid", "").strip()
    upwd = data.get("upwd", "").strip()

    if not uname or not uid or not upwd:
        return jsonify({"success": False, "message": "이름, 아이디, 비밀번호를 모두 입력하세요."}), 400

    sql = "INSERT INTO member (uname, uid, upwd, datetime) VALUES (?, ?, ?, ?)"
    params = (uname, uid, upwd, now_str())

    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        conn.close()
        log_query(sql, params)
        return jsonify({"success": True, "message": "회원가입 완료"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "이미 사용 중인 아이디입니다."}), 409


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    uid = data.get("uid", "").strip()
    upwd = data.get("upwd", "").strip()

    sql = "SELECT idx, uname, uid FROM member WHERE uid = ? AND upwd = ?"
    params = (uid, upwd)

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    user = cur.fetchone()
    conn.close()
    log_query(sql, params)

    if user:
        session["uid"] = user["uid"]
        session["uname"] = user["uname"]
        return jsonify({"success": True, "message": "로그인 성공", "uid": user["uid"], "uname": user["uname"]})

    return jsonify({"success": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "로그아웃 완료"})


@app.route("/todos", methods=["GET"])
def get_todos():
    if not login_required():
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    sql = "SELECT id, title, uid, completed, datetime FROM todolist WHERE uid = ? ORDER BY id DESC"
    params = (session["uid"],)

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    log_query(sql, params)

    todos = []
    for row in rows:
        todos.append({
            "id": row["id"],
            "title": row["title"],
            "uid": row["uid"],
            "completed": bool(row["completed"]),
            "datetime": row["datetime"]
        })

    return jsonify({"success": True, "todos": todos})


@app.route("/todos", methods=["POST"])
def add_todo():
    if not login_required():
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    data = request.get_json() or {}
    title = data.get("title", "").strip()

    if not title:
        return jsonify({"success": False, "message": "할 일을 입력하세요."}), 400

    sql = "INSERT INTO todolist (title, uid, completed, datetime) VALUES (?, ?, ?, ?)"
    params = (title, session["uid"], 0, now_str())

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    todo_id = cur.lastrowid
    conn.close()
    log_query(sql, params)

    return jsonify({"success": True, "message": "할 일이 추가되었습니다.", "id": todo_id})


@app.route("/todos/<int:todo_id>", methods=["PUT"])
def complete_todo(todo_id):
    if not login_required():
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    sql = "UPDATE todolist SET completed = 1 WHERE id = ? AND uid = ?"
    params = (todo_id, session["uid"])

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    affected = cur.rowcount
    conn.close()
    log_query(sql, params)

    if affected == 0:
        return jsonify({"success": False, "message": "수정할 할 일을 찾을 수 없습니다."}), 404

    return jsonify({"success": True, "message": "완료 처리되었습니다."})


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    if not login_required():
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    sql = "DELETE FROM todolist WHERE id = ? AND uid = ?"
    params = (todo_id, session["uid"])

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    affected = cur.rowcount
    conn.close()
    log_query(sql, params)

    if affected == 0:
        return jsonify({"success": False, "message": "삭제할 할 일을 찾을 수 없습니다."}), 404

    return jsonify({"success": True, "message": "삭제되었습니다."})


if __name__ == "__main__":
    init_sqlite_db()
    init_mysql_log_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
