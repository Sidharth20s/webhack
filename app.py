#!/usr/bin/env python3
"""
Pixel Prophet - Advanced CTF Challenge
A multi-layer file upload exploitation challenge
"""

import os
import subprocess
import base64
import pickle
import hashlib
import time
import random
import string
import sqlite3
import logging
from datetime import datetime
from io import BytesIO
from flask import (
    Flask, request, render_template,
    render_template_string, session, make_response,
    jsonify, redirect, url_for
)
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter
import re

# Setup logging
main_logger = logging.getLogger('app')
logging.basicConfig(level=logging.INFO, filename='logs/app.log', format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

# Advanced security configurations (all bypassable)
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
ALLOWED_MIMES = {'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'}

# Rate limiting (bypassable)
RATE_LIMIT = {}
BLACKLISTED_IPS = set()

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('flask_session', exist_ok=True)
os.makedirs('flags', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# ==================== LAYER 1: WAF Simulation ====================

class WAF:
    @staticmethod
    def check_request(ip, endpoint):
        """Simulate WAF with bypassable rules"""
        # Rate limiting (bypass with X-Forwarded-For)
        if ip in RATE_LIMIT:
            if time.time() - RATE_LIMIT[ip] < 1:
                return False
        RATE_LIMIT[ip] = time.time()
        
        # IP blacklisting (bypass with spoofed headers)
        if ip in BLACKLISTED_IPS:
            return False
            
        return True
    
    @staticmethod
    def sanitize_input(data):
        """Multiple sanitization layers (all bypassable)"""
        # Layer 1: Remove common patterns
        data = data.replace('../', '')
        data = data.replace('..\\', '')
        data = data.replace(';', '')
        data = data.replace('|', '')
        data = data.replace('&', '')
        
        # Layer 2: URL decode bypass
        data = data.replace('%2e%2e%2f', '')
        data = data.replace('%252e%252e%252f', '')
        
        # Layer 3: Unicode normalization bypass
        data = data.replace('\u2026', '')
        
        return data

waf = WAF()

# ==================== LAYER 2: Image Processing ====================

class ImageProcessor:
    @staticmethod
    def validate_image(file):
        """Multi-layer image validation"""
        # Layer 1: Check extension
        if '.' not in file.filename:
            return False, 'Invalid filename'
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f'Extension .{ext} not allowed'
        
        # Layer 2: Check MIME type
        if file.mimetype not in ALLOWED_MIMES:
            return False, f'MIME type {file.mimetype} not allowed'
        
        # Layer 3: Magic bytes
        magic_bytes = file.read(8)
        file.seek(0)
        
        if ext in ['jpg', 'jpeg'] and magic_bytes[:2] != b'\xff\xd8':
            return False, 'Invalid JPEG header'
        elif ext == 'png' and magic_bytes[:8] != b'\x89PNG\r\n\x1a\n':
            return False, 'Invalid PNG header'
        elif ext == 'gif' and magic_bytes[:6] not in [b'GIF87a', b'GIF89a']:
            return False, 'Invalid GIF header'
        
        # Layer 4: Try to open with PIL (preserves metadata)
        try:
            img = Image.open(file)
            # Generate unique filename
            filename = hashlib.sha256(
                file.filename.encode() + str(time.time()).encode()
            ).hexdigest()[:16] + '.' + ext
            
            # Process based on image type
            if ext in ['jpg', 'jpeg']:
                # VULNERABILITY: Preserves EXIF data with PHP
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), 
                        'JPEG', quality=85, exif=img.info.get('exif', b''))
            elif ext == 'png':
                # VULNERABILITY: Preserves tEXt chunks
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'PNG')
            elif ext == 'gif':
                # VULNERABILITY: Preserves application extensions
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'GIF')
            
            return True, filename
            
        except Exception as e:
            return False, f'Image processing failed: {str(e)}'

processor = ImageProcessor()

# ==================== LAYER 3: Advanced Authentication ====================

class AuthManager:
    def __init__(self):
        self.users = {
            'admin': {
                'password': self.hash_password('super_secret_admin_2024'),
                '2fa_secret': self.generate_2fa(),
                'role': 'admin'
            },
            'guest': {
                'password': self.hash_password('guest'),
                '2fa_secret': None,
                'role': 'user'
            }
        }
        self.tokens = {}
        self.sessions = {}
    
    def hash_password(self, password):
        """Weak hashing (vulnerable to timing attacks)"""
        time.sleep(0.01)  # Timing attack vector
        return hashlib.md5(password.encode()).hexdigest()
    
    def generate_2fa(self):
        """Predictable 2FA (vulnerable)"""
        return str(int(time.time()) % 1000000).zfill(6)
    
    def authenticate(self, username, password, token=None):
        if username not in self.users:
            return False
        
        user = self.users[username]
        if user['password'] != self.hash_password(password):
            return False
        
        # VULNERABILITY: 2FA bypass possible
        if user['2fa_secret'] and token != user['2fa_secret']:
            return False
        
        # Generate session token
        session_token = hashlib.sha256(
            (username + str(time.time())).encode()
        ).hexdigest()
        
        self.tokens[session_token] = {
            'username': username,
            'role': user['role'],
            'expires': time.time() + 3600
        }
        
        return session_token
    
    def verify_token(self, token):
        if token not in self.tokens:
            return None
        if self.tokens[token]['expires'] < time.time():
            del self.tokens[token]
            return None
        return self.tokens[token]

auth = AuthManager()

# ==================== LAYER 4: API Endpoints ====================

@app.route('/')
def index():
    """Main page with hidden clues"""
    return render_template('index.html', 
                         version='2.5.3-beta',
                         build='2024.03.15-19:42',
                         server=request.headers.get('Server', 'Unknown'))

@app.route('/api/v1/upload', methods=['POST'])
def api_upload():
    """VULNERABLE: File upload endpoint"""
    # WAF check
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if not waf.check_request(client_ip, '/api/v1/upload'):
        return jsonify({'error': 'Rate limited'}), 429
    
    # Authentication check
    auth_token = request.headers.get('X-Auth-Token')
    if not auth_token or not auth.verify_token(auth_token):
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Process image
    success, result = processor.validate_image(file)
    if not success:
        return jsonify({'error': result}), 400
    
    # Return file info
    return jsonify({
        'status': 'success',
        'filename': result,
        'url': f'/uploads/{result}',
        'size': os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], result))
    })

@app.route('/api/v1/process')
def api_process():
    """VULNERABLE: Image processing with command injection"""
    # Authentication check
    auth_token = request.headers.get('X-Auth-Token')
    user_data = auth.verify_token(auth_token)
    
    if not user_data or user_data['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    filename = request.args.get('file', '')
    operation = request.args.get('op', 'resize')
    
    # WAF sanitization (bypassable)
    filename = waf.sanitize_input(filename)
    operation = waf.sanitize_input(operation)
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # VULNERABILITY: Command injection in imagemagick
        # Players can do: ; cat /etc/passwd #
        cmd = f'convert {filepath} -{operation} output.jpg 2>&1'
        result = subprocess.check_output(cmd, shell=True, timeout=5)
        
        return jsonify({
            'status': 'success',
            'output': result.decode(),
            'operation': operation
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Processing timeout'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/auth/login', methods=['POST'])
def api_login():
    """VULNERABLE: Authentication endpoint"""
    data = request.get_json()
    
    username = data.get('username', '')
    password = data.get('password', '')
    token = data.get('2fa_token', '')
    
    # VULNERABILITY: Timing attack possible
    # Also vulnerable to SQL injection if we used SQL
    session_token = auth.authenticate(username, password, token)
    
    if session_token:
        return jsonify({
            'status': 'success',
            'token': session_token,
            'role': auth.tokens[session_token]['role']
        })
    else:
        return jsonify({'error': 'Authentication failed'}), 401

@app.route('/api/v1/admin/debug')
def api_debug():
    """VULNERABLE: Debug endpoint with RCE"""
    # Check admin token
    auth_token = request.headers.get('X-Auth-Token')
    user_data = auth.verify_token(auth_token)
    
    if not user_data or user_data['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    cmd = request.args.get('cmd', 'id')
    
    # VULNERABILITY: Direct command execution
    try:
        output = subprocess.check_output(cmd, shell=True, timeout=5)
        return jsonify({
            'status': 'success',
            'command': cmd,
            'output': base64.b64encode(output).decode()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/admin/session')
def api_session():
    """VULNERABLE: Session manipulation"""
    # Check admin token
    auth_token = request.headers.get('X-Auth-Token')
    user_data = auth.verify_token(auth_token)
    
    if not user_data or user_data['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    session_data = request.args.get('data', '')
    
    try:
        # VULNERABILITY: Pickle deserialization
        decoded = base64.b64decode(session_data)
        obj = pickle.loads(decoded)
        return jsonify({'status': 'success', 'data': str(obj)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    # WAF sanitization
    filename = waf.sanitize_input(filename)
    
    # VULNERABILITY: Path traversal in filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):
        return open(filepath, 'rb').read()
    return 'File not found', 404

@app.route('/logs')
def view_logs():
    """VULNERABLE: Log viewing with LFI"""
    # Hidden endpoint - not documented
    if request.remote_addr != '127.0.0.1':
        return 'Access Denied', 403
    
    logfile = request.args.get('file', 'access.log')
    
    # VULNERABILITY: Path traversal
    logpath = os.path.join('logs', logfile)
    
    if os.path.exists(logpath):
        return f'<pre>{open(logpath).read()}</pre>'
    return 'Log not found', 404

@app.route('/robots.txt')
def robots():
    """Information disclosure"""
    return '''
User-agent: *
Disallow: /api/
Disallow: /admin/
Disallow: /logs/
Disallow: /backup/

# API documentation at /api/v1/docs
# Version: 2.5.3-beta
# Build: 2024.03.15-19:42
'''

@app.route('/api/v1/docs')
def api_docs():
    """API documentation (leaks endpoints)"""
    return jsonify({
        'endpoints': [
            {'path': '/api/v1/upload', 'method': 'POST', 'auth': 'required'},
            {'path': '/api/v1/process', 'method': 'GET', 'auth': 'admin'},
            {'path': '/api/v1/auth/login', 'method': 'POST', 'auth': 'none'},
            {'path': '/api/v1/admin/debug', 'method': 'GET', 'auth': 'admin'},
            {'path': '/api/v1/admin/session', 'method': 'GET', 'auth': 'admin'}
        ],
        'version': '2.5.3-beta',
        'build': '2024.03.15-19:42'
    })

@app.route('/backup/')
def backup():
    """Hidden backup directory"""
    return '''
    <h1>Backups</h1>
    <ul>
        <li><a href="/backup/app.py.bak">app.py.bak</a></li>
        <li><a href="/backup/config.json">config.json</a></li>
        <li><a href="/backup/.env">.env</a></li>
    </ul>
    '''

@app.route('/backup/app.py.bak')
def backup_app():
    """Source code leak"""
    return open(__file__, 'r').read()

@app.route('/backup/config.json')
def backup_config():
    """Config leak with credentials"""
    return jsonify({
        'database': {
            'host': 'localhost',
            'user': 'app_user',
            'password': 'app_pass_2024'
        },
        'api_keys': {
            'internal': 'sk_live_1234567890abcdef'
        },
        'debug': True,
        'secret_key': app.secret_key
    })

@app.errorhandler(404)
def not_found(error):
    """Custom 404 page with hidden data"""
    return render_template_string('''
        <h1>404 - Not Found</h1>
        <p>The requested resource was not found.</p>
        <!-- Debug: Check /api/v1/docs for available endpoints -->
        <!-- Server: {{ server }} -->
        <!-- Time: {{ time }} -->
    '''.format(
        server=request.headers.get('Server', 'Unknown'),
        time=time.time()
    )), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

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
