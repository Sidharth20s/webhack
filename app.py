#!/usr/bin/env python3
"""
Advanced CTF Challenge: File Upload Mayhem
Multiple exploitation stages with intentional vulnerabilities
"""

from flask import (
    Flask, request, render_template, 
    render_template_string, session, make_response, redirect, jsonify, send_file
)
from werkzeug.utils import secure_filename
from PIL import Image
import sqlite3
import os
import subprocess
import time
import hashlib
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import json
from io import BytesIO
import threading

app = Flask(__name__)
app.secret_key = 'super_secret_key_2024'  # Intentionally weak - CTF vulnerability

# Configuration with intentional vulnerabilities
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = False  # VULNERABILITY: No session signing

# Create necessary directories
for directory in [app.config['UPLOAD_FOLDER'], app.config['SESSION_FILE_DIR'], 'logs', 'uploads', 'static']:
    os.makedirs(directory, exist_ok=True)

# Setup logging
def setup_logging():
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.DEBUG)
    
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    main_handler = RotatingFileHandler('logs/app.log', maxBytes=10*1024*1024, backupCount=5)
    main_handler.setFormatter(detailed_formatter)
    main_logger.addHandler(main_handler)
    
    return main_logger

main_logger = setup_logging()

# Initialize database
def init_db():
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT, role TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS posts
                     (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT, created_at TEXT)''')
        
        try:
            c.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@vulnerable.local', 'admin')")
            c.execute("INSERT INTO users VALUES (2, 'user1', 'password', 'user1@vulnerable.local', 'user')")
            c.execute("INSERT INTO users VALUES (3, 'user2', '12345', 'user2@vulnerable.local', 'user')")
        except:
            pass
        
        conn.commit()
    except Exception as e:
        main_logger.error(f"Database initialization error: {str(e)}")
    finally:
        conn.close()

init_db()

# ========== VULNERABILITY 1: INFORMATION DISCLOSURE ==========
@app.route('/robots.txt')
def robots():
    """VULNERABILITY: Discloses hidden administrator paths"""
    return '''User-agent: *
Disallow: /admin
Disallow: /backup
Disallow: /console
Disallow: /flask_session
Disallow: /config
Allow: /static/uploads
'''

@app.route('/backup')
def backup():
    """VULNERABILITY: Directory listing of sensitive backups"""
    return '''
    <html>
    <head><title>Backup Directory</title></head>
    <body>
    <h1>Backup Directory</h1>
    <p>The following backups are available:</p>
    <ul>
        <li><a href="/backup/app.py.bak">app.py.bak</a> - Application source code</li>
        <li><a href="/backup/config.txt">config.txt</a> - Configuration file</li>
        <li><a href="/backup/.htaccess">.htaccess</a> - Apache configuration</li>
        <li><a href="/backup/database.bak">database.bak</a> - Database dump</li>
    </ul>
    </body>
    </html>
    '''

@app.route('/backup/app.py.bak')
def backup_app():
    """VULNERABILITY: Source code disclosure"""
    try:
        with open(__file__, 'r') as f:
            return f.read()
    except:
        return "Backup not accessible", 404

@app.route('/backup/config.txt')
def backup_config():
    """VULNERABILITY: Configuration and credential disclosure"""
    config_content = f"""
DATABASE_URL: sqlite:///vulnerable.db
DATABASE_PASSWORD: admin123
ADMIN_PASSWORD: flag{{info_disclosure_vulnerability}}
API_KEY: sk-1234567890abcdefghij
JWT_SECRET: very_secret_jwt_key_2024
STRIPE_KEY: sk_test_123456789abcdef
AWS_ACCESS_KEY: AKIAIOSFODNN7EXAMPLE
AWS_SECRET_KEY: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
DATABASE_ADMIN_PASSWORD: root_db_pass_123
ROOT_FLAG: flag{{source_code_exposed}}
    """
    return f"<pre>{config_content}</pre>"

@app.route('/backup/.htaccess')
def backup_htaccess():
    """VULNERABILITY: Apache configuration disclosure - shows PHP execution in uploads"""
    htaccess = """
# CRITICAL VULNERABILITY: Allows PHP execution on uploaded images
AddType application/x-httpd-php .jpg .jpeg .png .gif

# Additional dangerous configurations
php_flag display_errors on
php_value max_execution_time 300
php_value upload_max_filesize 100M

# If .htaccess is placed in uploads folder, PHP code executes
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} -f
RewriteRule ^.*\\.(jpg|jpeg|png|gif)$ - [L]
    """
    return f"<pre>{htaccess}</pre>"

@app.route('/backup/database.bak')
def backup_database():
    """VULNERABILITY: Database backup disclosure"""
    try:
        with open('vulnerable.db', 'rb') as f:
            content = f.read()
        return send_file(BytesIO(content), mimetype='application/octet-stream', download_name='vulnerable.db.bak')
    except:
        return "No backup available", 404

# ========== VULNERABILITY 2: SQL INJECTION ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login with SQL injection vulnerability"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        client_ip = request.remote_addr
        
        # VULNERABLE: SQL Injection - direct string interpolation
        conn = sqlite3.connect('vulnerable.db')
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        
        try:
            c.execute(query)
            user = c.fetchone()
            conn.close()
            
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[4]
                main_logger.info(f"User login: {username} from {client_ip}")
                return redirect('/dashboard')
            else:
                main_logger.warning(f"Failed login: {username} from {client_ip}")
                return render_template('login.html', error='Invalid credentials')
        except Exception as e:
            main_logger.error(f"SQL error: {str(e)}")
            return render_template('login.html', error=f'Error: {str(e)}')
    
    return render_template('login.html')

# ========== VULNERABILITY 2: FILE UPLOAD WITH MULTI-LAYER BYPASS ==========
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """File upload with multiple bypassable validation layers"""
    if 'user_id' not in session:
        main_logger.warning(f"Upload access denied (not logged in) from {request.remote_addr}")
        return redirect('/login')
    
    if request.method == 'GET':
        return render_template('upload.html')
    
    if 'file' not in request.files:
        main_logger.warning(f"Upload attempt without file from {request.remote_addr}")
        return "No file provided", 400
    
    file = request.files['file']
    username = session.get('username', 'Unknown')
    client_ip = request.remote_addr
    
    if not file or not file.filename:
        return "No file selected", 400
    
    # LAYER 1: Extension whitelist check (BYPASS: .php5, .phtml, .phps, double extension)
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        main_logger.warning(f"Upload rejected: {file_ext} extension from {username}")
        return "Invalid extension. Only .jpg, .jpeg, .png, .gif allowed", 400
    
    # LAYER 2: MIME type check (BYPASS: Change Content-Type header)
    allowed_mimes = ['image/jpeg', 'image/png', 'image/gif']
    if file.mimetype not in allowed_mimes:
        main_logger.warning(f"Upload rejected: {file.mimetype} MIME type from {username}")
        return "Invalid MIME type", 400
    
    # LAYER 3: Magic byte verification (BYPASS: Polyglot files with valid image headers + PHP)
    file_data = file.read()
    file.seek(0)
    
    magic_bytes = {
        b'\xFF\xD8\xFF': 'jpeg',
        b'\x89\x50\x4E\x47': 'png',
        b'\x47\x49\x46': 'gif'
    }
    
    valid_magic = False
    for magic, fmt in magic_bytes.items():
        if file_data.startswith(magic):
            valid_magic = True
            break
    
    if not valid_magic:
        main_logger.warning(f"Upload rejected: Invalid magic bytes from {username}")
        return "Invalid magic bytes - not a valid image", 400
    
    # LAYER 4: Image processing (VULNERABILITY: PIL doesn't strip EXIF/comments containing PHP)
    try:
        img = Image.open(BytesIO(file_data))
        img.thumbnail((800, 600))
        output = BytesIO()
        # VULNERABILITY: Embedded PHP in EXIF/comments survives
        img.save(output, format=img.format if img.format else 'JPEG', quality=85)
        processed_data = output.getvalue()
    except Exception as e:
        main_logger.error(f"Image processing failed: {str(e)}")
        processed_data = file_data
    
    # VULNERABILITY 3: PATH TRAVERSAL - Weak sanitization
    filename = file.filename
    # VULNERABLE: Only removes '../' once - can be bypassed with '....//'
    safe_filename = filename.replace('../', '')
    
    # Check if still contains path traversal
    if '../' in safe_filename or '..\\' in safe_filename:
        main_logger.warning(f"Path traversal attempt detected: {filename} from {username}")
    
    # Save file to uploads folder
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    
    # VULNERABILITY 4: RACE CONDITION - No locking on concurrent uploads
    time.sleep(0.01)  # Simulate window for race condition
    
    try:
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        with open(upload_path, 'wb') as f:
            f.write(processed_data)
        
        # VULNERABILITY 3: LOG POISONING - User-Agent not sanitized
        user_agent = request.headers.get('User-Agent', 'Unknown')
        main_logger.info(f"File uploaded: {safe_filename} | User-Agent: {user_agent}")
        
        return f'''<html><body>
        <h2>Upload Successful!</h2>
        <p>File '<strong>{safe_filename}</strong>' uploaded.</p>
        <ul>
        <li>✓ Extension check passed</li>
        <li>✓ MIME type verified</li>
        <li>✓ Magic bytes validated</li>
        <li>✓ Image processed</li>
        </ul>
        <p><a href="/static/uploads/{safe_filename}">View file</a></p>
        <p><a href="/upload">Upload another</a></p>
        </body></html>'''
    except Exception as e:
        main_logger.error(f"Upload error: {str(e)}")
        return f"Upload error: {str(e)}", 500

# ========== VULNERABILITY 3: PATH TRAVERSAL ==========
@app.route('/view')
def view():
    """VULNERABILITY: Path traversal to access arbitrary files"""
    filename = request.args.get('file', '')
    
    if not filename:
        return "No file specified", 400
    
    # VULNERABLE: Only removes '../' once - can be bypassed!
    # Bypass: /view?file=....//../etc/passwd becomes ../../etc/passwd
    # Bypass: /view?file=....//....//etc/passwd
    safe_filename = filename.replace('../', '')
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    
    # VULNERABILITY: SSTI when file is rendered as template
    try:
        with open(filepath, 'r', errors='ignore') as f:
            content = f.read()
        
        main_logger.info(f"File viewed: {safe_filename}")
        
        # CRITICAL VULNERABILITY: Renders user-controlled content as Jinja2 template
        # If attacker uploads file with template syntax, code executes
        return render_template_string(content)
    except FileNotFoundError:
        return "File not found", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

# ========== VULNERABILITY 4: COMMAND INJECTION & SSTI ==========
@app.route('/admin/ping')
def admin_ping():
    """VULNERABILITY: Command injection through weak admin cookie check"""
    # WEAK SECURITY: Admin check via client-side cookie (easily forged)
    if request.cookies.get('admin') != 'true':
        return 'Access Denied - Set admin=true cookie', 403
    
    ip = request.args.get('ip', '127.0.0.1')
    
    # VULNERABILITY: Command injection in subprocess
    try:
        # DANGEROUS: shell=True with user input
        result = subprocess.run(
            f'ping -c 3 {ip}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return f'<pre>{result.stdout}\n{result.stderr}</pre>'
    except subprocess.TimeoutExpired:
        return "Command timed out", 500
    except Exception as e:
        return f"Error: {str(e)}", 500

# ========== VULNERABILITY 4: RACE CONDITION IN SESSION HANDLING ==========
@app.route('/api/rapid-upload', methods=['POST'])
def rapid_upload():
    """VULNERABILITY: Race condition with concurrent file uploads"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    files = request.files.getlist('files')
    results = []
    
    # RACE CONDITION: Process files with minimal delay
    for file in files:
        # Small sleep creates window for race condition attacks
        time.sleep(0.01)
        
        if file and file.filename:
            filename = file.filename
            safe_filename = filename.replace('../', '')  # Same weak sanitization
            
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            
            # VULNERABLE: No proper locking - multiple threads can write same file
            file.save(upload_path)
            results.append(safe_filename)
    
    return jsonify({'uploaded': results})

# ========== VULNERABILITY 5: PRIVILEGE ESCALATION VECTORS ==========
@app.route('/admin/system-info')
def system_info():
    """VULNERABILITY: Information disclosure about system privileges"""
    # Weak admin check
    if request.cookies.get('admin') != 'true':
        return 'Access Denied', 403
    
    import sys
    import platform
    
    try:
        # Disclose system information
        info = {
            'os': platform.system(),
            'python': sys.version,
            'cwd': os.getcwd(),
            'user': os.getenv('USER') or os.getenv('USERNAME'),
            'upload_perms': oct(os.stat(app.config['UPLOAD_FOLDER']).st_mode)[-3:] if os.path.exists(app.config['UPLOAD_FOLDER']) else 'N/A',
            'flag_part': 'flag{privilege_escalation_'
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/exec', methods=['POST'])
def admin_exec():
    """VULNERABILITY: Direct command execution via admin panel"""
    if request.cookies.get('admin') != 'true':
        return jsonify({'error': 'Access Denied'}), 403
    
    command = request.form.get('cmd', '')
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    try:
        # DANGEROUS: shell=True allows full shell command execution
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return jsonify({
            'command': command,
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode,
            'flag_hint': 'flag{command_execution_via_admin_panel}'
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Command timeout'}), 500

@app.route('/admin/readflag')
def readflag():
    """VULNERABILITY: SUID binary emulation for flag reading"""
    if request.cookies.get('admin') != 'true':
        return jsonify({'error': 'Access Denied'}), 403
    
    # Simulate reading flag as root (would be SUID binary on real system)
    try:
        # Check if we can read /root directory (privilege check)
        if os.path.exists('/root') or os.path.exists('C:\\Windows\\System32'):
            flag = 'flag{privilege_escalation_suid_binary_executed}'
        else:
            flag = 'flag{not_running_as_root}'
        
        return jsonify({'flag': flag})
    except:
        return jsonify({'flag': 'flag{not_running_as_root}'}), 403

@app.route('/dashboard')
def dashboard():
    """Dashboard view"""
    if 'user_id' not in session:
        return redirect('/login')
    
    username = session.get('username', 'Unknown')
    return render_template('dashboard.html', username=username)

@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')
        
        conn = sqlite3.connect('vulnerable.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users VALUES (NULL, ?, ?, ?, ?)",
                     (username, password, email, 'user'))
            conn.commit()
            return redirect('/login')
        except:
            return render_template('register.html', error='Username already exists')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/logs')
def view_logs():
    """VULNERABILITY: Unprotected log viewing endpoint"""
    log_type = request.args.get('type', 'all')
    
    logs_content = ""
    try:
        with open('logs/app.log', 'r') as f:
            logs_content = f.read()
    except:
        logs_content = "No logs available"
    
    # Log poisoning vulnerability: User-Agent already logged
    return f'''<html><body>
    <h2>Application Logs</h2>
    <pre>{logs_content}</pre>
    </body></html>'''

if __name__ == '__main__':
    main_logger.info("=" * 80)
    main_logger.info("APPLICATION STARTED - CTF CHALLENGE")
    main_logger.info(f"Timestamp: {datetime.now().isoformat()}")
    main_logger.info("=" * 80)
    app.run(debug=True, host='0.0.0.0', port=5000)
