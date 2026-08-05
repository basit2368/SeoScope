import os
import json
import sqlite3
import datetime
import logging

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL Configuration defaults
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DB = os.environ.get('MYSQL_DB', 'seoscope_db')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

# Flag to track active DB type: 'mysql' or 'sqlite'
ACTIVE_DB_TYPE = 'sqlite'
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'seoscope.db')


def get_mysql_raw_connection(select_db=True):
    """Attempt raw connection to MySQL server."""
    if not PYMYSQL_AVAILABLE:
        raise ConnectionError("PyMySQL library is not installed.")
    
    kwargs = {
        'host': MYSQL_HOST,
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'port': MYSQL_PORT,
        'autocommit': True,
        'cursorclass': pymysql.cursors.DictCursor
    }
    if select_db:
        kwargs['database'] = MYSQL_DB
    
    return pymysql.connect(**kwargs)


def init_db():
    """
    Initializes database tables.
    Tries MySQL first. If MySQL fails, falls back to SQLite.
    """
    global ACTIVE_DB_TYPE

    # Try initializing MySQL
    if PYMYSQL_AVAILABLE:
        try:
            # First connect without DB to ensure DB exists
            conn = get_mysql_raw_connection(select_db=False)
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()

            # Now connect to the database and create tables
            conn = get_mysql_raw_connection(select_db=True)
            with conn.cursor() as cursor:
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        password VARCHAR(255) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # Audit Reports table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_reports (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NULL,
                        website_url VARCHAR(500) NOT NULL,
                        seo_score INT NOT NULL,
                        technical_score INT DEFAULT 0,
                        content_score INT DEFAULT 0,
                        images_score INT DEFAULT 0,
                        links_score INT DEFAULT 0,
                        audit_data LONGTEXT NOT NULL,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
            conn.close()
            ACTIVE_DB_TYPE = 'mysql'
            logger.info(f"Successfully connected to MySQL database: `{MYSQL_DB}`")
            return 'mysql'
        except Exception as e:
            logger.warning(f"MySQL connection/initialization failed ({e}). Falling back to SQLite.")

    # SQLite Fallback
    ACTIVE_DB_TYPE = 'sqlite'
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            website_url TEXT NOT NULL,
            seo_score INTEGER NOT NULL,
            technical_score INTEGER DEFAULT 0,
            content_score INTEGER DEFAULT 0,
            images_score INTEGER DEFAULT 0,
            links_score INTEGER DEFAULT 0,
            audit_data TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    """)

    conn.commit()
    conn.close()
    logger.info(f"Successfully initialized SQLite database at {SQLITE_PATH}")
    return 'sqlite'


def get_db():
    """Returns DB connection or helper context depending on ACTIVE_DB_TYPE."""
    if ACTIVE_DB_TYPE == 'mysql':
        try:
            return get_mysql_raw_connection(select_db=True)
        except Exception as e:
            logger.error(f"MySQL connection error during request: {e}. Switching to SQLite.")
            return sqlite3.connect(SQLITE_PATH)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def create_user(name, email, password_hash):
    """Creates a new user record."""
    conn = get_db()
    if ACTIVE_DB_TYPE == 'mysql' and isinstance(conn, pymysql.Connection):
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, password_hash)
                )
                user_id = cursor.lastrowid
            conn.close()
            return user_id
        except Exception as e:
            conn.close()
            raise e
    else:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id


def get_user_by_email(email):
    """Retrieves user by email."""
    conn = get_db()
    if ACTIVE_DB_TYPE == 'mysql' and isinstance(conn, pymysql.Connection):
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
            conn.close()
            return user
        except Exception as e:
            conn.close()
            return None
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None


def get_user_by_id(user_id):
    """Retrieves user by user ID."""
    conn = get_db()
    if ACTIVE_DB_TYPE == 'mysql' and isinstance(conn, pymysql.Connection):
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
            conn.close()
            return user
        except Exception as e:
            conn.close()
            return None
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None


def save_audit_report(user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, audit_data):
    """Saves an SEO audit report."""
    audit_data_str = json.dumps(audit_data) if isinstance(audit_data, (dict, list)) else str(audit_data)
    conn = get_db()
    
    if ACTIVE_DB_TYPE == 'mysql' and isinstance(conn, pymysql.Connection):
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO audit_reports 
                    (user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, audit_data, date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, audit_data_str))
                report_id = cursor.lastrowid
            conn.close()
            return report_id
        except Exception as e:
            conn.close()
            logger.error(f"Failed to save report to MySQL: {e}")
            raise e
    else:
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO audit_reports 
            (user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, audit_data, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, audit_data_str, now_str))
        conn.commit()
        report_id = cursor.lastrowid
        conn.close()
        return report_id


def get_all_audit_reports(limit=50, user_id=None):
    """Fetches list of recent audit reports."""
    conn = get_db()
    if ACTIVE_DB_TYPE == 'mysql' and isinstance(conn, pymysql.Connection):
        try:
            with conn.cursor() as cursor:
                if user_id:
                    cursor.execute("""
                        SELECT id, user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, date 
                        FROM audit_reports WHERE user_id = %s ORDER BY id DESC LIMIT %s
                    """, (user_id, limit))
                else:
                    cursor.execute("""
                        SELECT id, user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, date 
                        FROM audit_reports ORDER BY id DESC LIMIT %s
                    """, (limit,))
                reports = cursor.fetchall()
            conn.close()
            return reports
        except Exception as e:
            conn.close()
            logger.error(f"Error fetching reports: {e}")
            return []
    else:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("""
                SELECT id, user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, date 
                FROM audit_reports WHERE user_id = ? ORDER BY id DESC LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT id, user_id, website_url, seo_score, technical_score, content_score, images_score, links_score, date 
                FROM audit_reports ORDER BY id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


def get_audit_report_by_id(report_id):
    """Retrieves single report by ID including full audit_data."""
    conn = get_db()
    if ACTIVE_DB_TYPE == 'mysql' and isinstance(conn, pymysql.Connection):
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM audit_reports WHERE id = %s", (report_id,))
                report = cursor.fetchone()
            conn.close()
            if report and 'audit_data' in report and isinstance(report['audit_data'], str):
                report['audit_data'] = json.loads(report['audit_data'])
            return report
        except Exception as e:
            conn.close()
            logger.error(f"Error getting report {report_id}: {e}")
            return None
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            report = dict(row)
            if 'audit_data' in report and isinstance(report['audit_data'], str):
                report['audit_data'] = json.loads(report['audit_data'])
            return report
        return None


def delete_audit_report(report_id):
    """Deletes audit report by ID."""
    conn = get_db()
    if ACTIVE_DB_TYPE == 'mysql' and isinstance(conn, pymysql.Connection):
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM audit_reports WHERE id = %s", (report_id,))
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False
    else:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM audit_reports WHERE id = ?", (report_id,))
        conn.commit()
        conn.close()
        return True
