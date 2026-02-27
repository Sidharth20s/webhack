from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import json

app = Flask(__name__)
app.secret_key = 'insecure_secret_key_12345'  # Intentionally weak

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Configure logging
def setup_logging():
    # Main logger
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.DEBUG)
    
    # Success logger
    success_logger = logging.getLogger('success')
    success_logger.setLevel(logging.DEBUG)
    
    # Failure logger
    failure_logger = logging.getLogger('failure')
    failure_logger.setLevel(logging.DEBUG)
    
    # Changes logger
    changes_logger = logging.getLogger('changes')
    changes_logger.setLevel(logging.DEBUG)
    
    # Formatter
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Main log handler
    main_handler = RotatingFileHandler('logs/app.log', maxBytes=10*1024*1024, backupCount=5)
    main_handler.setFormatter(detailed_formatter)
    main_logger.addHandler(main_handler)
    
    # Success log handler
    success_handler = RotatingFileHandler('logs/success.log', maxBytes=10*1024*1024, backupCount=5)
    success_handler.setFormatter(detailed_formatter)
    success_logger.addHandler(success_handler)
    
    # Failure log handler
    failure_handler = RotatingFileHandler('logs/failure.log', maxBytes=10*1024*1024, backupCount=5)
    failure_handler.setFormatter(detailed_formatter)
    failure_logger.addHandler(failure_handler)
    
    # Changes log handler
    changes_handler = RotatingFileHandler('logs/changes.log', maxBytes=10*1024*1024, backupCount=5)
    changes_handler.setFormatter(detailed_formatter)
    changes_logger.addHandler(changes_handler)
    
    return main_logger, success_logger, failure_logger, changes_logger

main_logger, success_logger, failure_logger, changes_logger = setup_logging()

# Helper logging functions
def log_success(event, details=None):
    """Log successful events"""
    message = f"[SUCCESS] {event}"
    if details:
        message += f" | {json.dumps(details)}"
    success_logger.info(message)
    main_logger.info(message)

def log_failure(event, details=None):
    """Log failed events"""
    message = f"[FAILURE] {event}"
    if details:
        message += f" | {json.dumps(details)}"
    failure_logger.warning(message)
    main_logger.warning(message)

def log_change(event, details=None):
    """Log changes in the application"""
    message = f"[CHANGE] {event}"
    if details:
        message += f" | {json.dumps(details)}"
    changes_logger.info(message)
    main_logger.info(message)

# Initialize database
def init_db():
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT, role TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS posts
                     (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT, created_at TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS comments
                     (id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER, comment TEXT)''')
        
        # Insert sample users with weak passwords
        try:
            c.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@vulnerable.local', 'admin')")
            c.execute("INSERT INTO users VALUES (2, 'user1', 'password', 'user1@vulnerable.local', 'user')")
            c.execute("INSERT INTO users VALUES (3, 'user2', '12345', 'user2@vulnerable.local', 'user')")
            log_success("Database initialized", {"action": "created tables and inserted sample users"})
        except:
            log_change("Database already initialized", {"action": "tables and users already exist"})
        
        conn.commit()
    except Exception as e:
        log_failure("Database initialization error", {"error": str(e)})
    finally:
        conn.close()

init_db()

# Vulnerable login - SQL Injection possible
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        client_ip = request.remote_addr
        
        # VULNERABLE: SQL Injection vulnerability
        conn = sqlite3.connect('vulnerable.db')
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        c.execute(query)
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]
            log_success("User login", {"username": username, "user_id": user[0], "ip": client_ip})
            return redirect('/dashboard')
        else:
            log_failure("Login attempt failed", {"username": username, "ip": client_ip, "reason": "Invalid credentials"})
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    user_id = session.get('user_id', 'Unknown')
    session.clear()
    log_success("User logout", {"username": username, "user_id": user_id})
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        log_failure("Dashboard access denied", {"reason": "User not authenticated"})
        return redirect('/login')
    
    username = session.get('username', 'Unknown')
    user_id = session.get('user_id')
    
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    c.execute("SELECT * FROM posts")
    posts = c.fetchall()
    conn.close()
    
    log_success("Dashboard accessed", {"username": username, "user_id": user_id, "posts_count": len(posts)})
    return render_template('dashboard.html', posts=posts)

# Vulnerable search - XSS vulnerability
@app.route('/search')
def search():
    query = request.args.get('q', '')
    user_id = session.get('user_id', 'Unknown')
    username = session.get('username', 'Unknown')
    client_ip = request.remote_addr
    
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE title LIKE ?", (f'%{query}%',))
    results = c.fetchall()
    conn.close()
    
    # VULNERABLE: XSS - user input reflected without escaping
    html = f"<h2>Search results for: {query}</h2>"
    for post in results:
        html += f"<div><h3>{post[2]}</h3><p>{post[3]}</p></div>"
    
    log_success("Search performed", {"query": query, "username": username, "user_id": user_id, "results_count": len(results), "ip": client_ip})
    return html

# Vulnerable file upload - File upload vulnerability
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        log_failure("Upload access denied", {"reason": "User not authenticated"})
        return redirect('/login')
    
    username = session.get('username', 'Unknown')
    user_id = session.get('user_id')
    client_ip = request.remote_addr
    
    if request.method == 'POST':
        file = request.files.get('file')
        
        # VULNERABLE: No file type validation
        if file:
            filename = file.filename
            file.save(f'uploads/{filename}')
            log_change("File uploaded", {"filename": filename, "username": username, "user_id": user_id, "ip": client_ip})
            log_success("File upload completed", {"filename": filename, "size": len(file.read()), "user": username})
            return f"File {filename} uploaded successfully!"
        else:
            log_failure("File upload failed", {"reason": "No file provided", "username": username, "user_id": user_id})
            return "No file provided!"
    
    return render_template('upload.html')

# Vulnerable API - CSRF and API key vulnerability
@app.route('/api/post', methods=['POST'])
def api_post():
    # VULNERABLE: No CSRF token validation
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    user_id = session.get('user_id')
    username = session.get('username', 'Unknown')
    client_ip = request.remote_addr
    
    if not user_id:
        log_failure("API post request denied", {"reason": "Not authenticated", "ip": client_ip})
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO posts VALUES (NULL, ?, ?, ?, ?)",
                  (user_id, title, content, datetime.now().isoformat()))
        conn.commit()
        log_change("New post created via API", {"title": title[:50], "username": username, "user_id": user_id})
        log_success("API post request successful", {"username": username, "user_id": user_id, "ip": client_ip})
        return jsonify({'success': True})
    except Exception as e:
        log_failure("API post request failed", {"error": str(e), "username": username, "user_id": user_id, "ip": client_ip})
        return jsonify({'error': 'Failed to create post'}), 500
    finally:
        conn.close()

# Vulnerable info disclosure
@app.route('/user-info')
def user_info():
    user_id_param = request.args.get('id', '')
    requester_id = session.get('user_id', 'Unknown')
    requester_username = session.get('username', 'Unknown')
    client_ip = request.remote_addr
    
    # VULNERABLE: No authorization check - can view any user's info
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    c.execute(f"SELECT username, email FROM users WHERE id={user_id_param}")
    user = c.fetchone()
    conn.close()
    
    if user:
        log_success("User info accessed", {"requested_user_id": user_id_param, "requester_username": requester_username, "requester_id": requester_id, "ip": client_ip})
        return jsonify({'username': user[0], 'email': user[1]})
    else:
        log_failure("User info request - user not found", {"requested_user_id": user_id_param, "requester_username": requester_username, "requester_id": requester_id, "ip": client_ip})
        return jsonify({'error': 'User not found'}), 404

@app.route('/')
def index():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')
        client_ip = request.remote_addr
        
        conn = sqlite3.connect('vulnerable.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users VALUES (NULL, ?, ?, ?, ?)",
                     (username, password, email, 'user'))
            conn.commit()
            log_change("New user registered", {"username": username, "email": email, "ip": client_ip})
            log_success("User registration successful", {"username": username, "email": email})
            return redirect('/login')
        except Exception as e:
            log_failure("User registration failed", {"username": username, "email": email, "error": "Username already exists", "ip": client_ip})
            return render_template('register.html', error='Username already exists')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/')
def index():
    main_logger.info("Index page accessed")
    return redirect('/login')

# Log viewing endpoint (for CTF - to see all logs)
@app.route('/logs/view')
def view_logs():
    """View all logs - useful for CTF debugging"""
    log_type = request.args.get('type', 'all')  # all, success, failure, changes
    
    logs_content = ""
    
    try:
        if log_type in ['all', 'app']:
            with open('logs/app.log', 'r') as f:
                logs_content += "<h2>Main Application Log</h2><pre>" + f.read() + "</pre><hr>"
        
        if log_type in ['all', 'success']:
            with open('logs/success.log', 'r') as f:
                logs_content += "<h2>Success Log</h2><pre>" + f.read() + "</pre><hr>"
        
        if log_type in ['all', 'failure']:
            with open('logs/failure.log', 'r') as f:
                logs_content += "<h2>Failure Log</h2><pre>" + f.read() + "</pre><hr>"
        
        if log_type in ['all', 'changes']:
            with open('logs/changes.log', 'r') as f:
                logs_content += "<h2>Changes Log</h2><pre>" + f.read() + "</pre><hr>"
    except FileNotFoundError:
        logs_content = "<p>No logs found yet.</p>"
    
    html = f"""
    <html>
    <head>
        <title>Application Logs</title>
        <style>
            body {{ font-family: monospace; margin: 20px; }}
            h2 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; }}
            .nav {{ margin-bottom: 20px; }}
            a {{ margin-right: 15px; }}
        </style>
    </head>
    <body>
        <h1>Application Logs Viewer</h1>
        <div class="nav">
            <a href="?type=all">All Logs</a> |
            <a href="?type=app">App Log</a> |
            <a href="?type=success">Success Log</a> |
            <a href="?type=failure">Failure Log</a> |
            <a href="?type=changes">Changes Log</a>
        </div>
        {logs_content}
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    main_logger.info("=" * 80)
    main_logger.info("APPLICATION STARTED")
    main_logger.info(f"Timestamp: {datetime.now().isoformat()}")
    main_logger.info("=" * 80)
    app.run(debug=True, port=5000)
