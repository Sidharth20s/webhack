# Vulnerable Web Application for Cybersecurity Learning

This is an **intentionally vulnerable** web application designed for educational purposes. It's a safe, legal practice environment for learning cybersecurity and ethical hacking.

## ⚠️ IMPORTANT
- **ONLY use this on your own machine or with permission**
- **DO NOT deploy this online**
- This app has deliberate security flaws for learning purposes

## Vulnerabilities Included

1. **SQL Injection** - Login form accepts SQL queries
2. **Cross-Site Scripting (XSS)** - Search functionality reflects user input
3. **Broken Access Control** - User info disclosure without authorization
4. **Weak Authentication** - Hardcoded weak passwords
5. **CSRF** - No CSRF token validation on forms
6. **Insecure File Upload** - No file type validation
7. **Information Disclosure** - Debug mode enabled, test credentials visible

## Setup Instructions

### 1. Install Python (if not installed)
Download from https://www.python.org/

### 2. Navigate to the project directory
```
cd c:\Users\SIDHARTH\OneDrive\Desktop\webhack
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Run the application
```
python app.py
```

The app will start on `http://localhost:5000`

## Test Credentials

- **Admin Account**
  - Username: `admin`
  - Password: `admin123`

- **User Account**
  - Username: `user1`
  - Password: `password`

## Learning Exercises

### Exercise 1: SQL Injection
1. Go to login page
2. In username field, try: `admin' --`
3. Leave password blank and login
4. **Goal:** Bypass login without password

### Exercise 2: XSS Attack
1. Login first
2. Go to search page
3. Try searching: `<img src=x onerror="alert('XSS')">`
4. **Goal:** Execute JavaScript in the page

### Exercise 3: Information Disclosure
1. Visit `/user-info?id=2` to see user 2's info
2. Try `/user-info?id=3` to see other users
3. **Goal:** Access unauthorized user data

### Exercise 4: Weak Passwords
1. Try common passwords on test accounts
2. **Goal:** Crack the password hashes

### Exercise 5: File Upload
1. Try uploading a `.php` or `.exe` file
2. **Goal:** Upload executable code

## Tools to Use for Testing

- **Burp Suite Community** - Intercept and modify requests
- **OWASP ZAP** - Automated vulnerability scanning
- **Browser DevTools** - Inspect and modify requests
- **SQLMap** - Automated SQL injection testing
- **curl** - Command-line HTTP requests

## Example: Testing SQL Injection with curl

```bash
curl -d "username=admin' OR '1'='1&password=anything" http://localhost:5000/login
```

## Learning Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackTheBox: https://www.hackthebox.com/
- TryHackMe: https://tryhackme.com/

## Disclaimer

This application is for educational purposes only. Use it to learn cybersecurity concepts on your own machine. Unauthorized access to computer systems is illegal. Always get permission before testing security on any system.

---
**Happy learning! 🔒**
