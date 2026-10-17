# Vulnerability Write-Up: SQL Injection & Reflected XSS in a Flask Web Application

**Author:** Ruben George
**Date:** October 2026
**Target:** Deliberately vulnerable Flask application (`vulnerable-app.py`), built for this project
**Fixed version:** `secure_app.py`

## 1. Summary

This document details two vulnerabilities discovered and deliberately introduced into a small Flask web application built for this project: a **SQL Injection** vulnerability in the login form, and a **Reflected Cross-Site Scripting (XSS)** vulnerability in the search feature. Both were manually exploited, automated via a Python proof-of-concept script, and subsequently remediated. This report covers the root cause, exploitation method, impact, and fix for each.

---

## 2. Vulnerability 1: SQL Injection (Login Form)

### 2.1 Description

The login route in `vulnerable-app.py` builds its SQL query by directly concatenating raw, unvalidated user input into the query string:

```python
query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
cursor.execute(query)
```

Because the `username` and `password` values submitted through the login form are inserted directly into the SQL command text, an attacker can submit input that alters the structure and logic of the query itself, rather than being treated as plain data to search for.

### 2.2 Exploitation

**Initial attempt:** submitting `' OR '1'='1` as the username failed to bypass the login. Inspecting the generated query revealed why:

```sql
SELECT * FROM users WHERE username = '' OR '1'='1' AND password = ''
```

Due to SQL's operator precedence, `AND` binds more tightly than `OR`, so this is evaluated as `username = '' OR ('1'='1' AND password = '')`. Since no user has an empty password, this clause evaluates to false, and the overall condition remains false.

**Working payload:** submitting `' OR '1'='1' -- ` as the username succeeded. The `--` sequence begins a SQL comment, causing everything after it (including the `AND password = '...'` clause) to be ignored by the database:

```sql
SELECT * FROM users WHERE username = '' OR '1'='1' -- ' AND password = ''
```

The effective query becomes `SELECT * FROM users WHERE username = '' OR '1'='1'`, which is always true and returns every row in the `users` table. The application then logs the attacker in as the first matching user, without requiring any valid password.

**Automation:** this exploit was scripted in `exploits/sql_exploits.py` using Python's `requests` library, sending the payload via an HTTP POST request and checking the response for a successful-login indicator. This confirmed the vulnerability was reliably reproducible outside manual browser testing.

### 2.3 Impact

An attacker with no valid credentials can fully bypass authentication and gain access to any account, including the first-registered (often administrative) user. In a real application, this could lead to unauthorised access to personal data, administrative functions, or further exploitation (e.g. using `UNION SELECT` to extract data from other tables).

### 2.4 Root Cause

User input was treated as part of the executable SQL command rather than as data. The application trusted that input would always match the intended format (a plain username/password) and provided no separation between code and data.

### 2.5 Remediation

The fix, implemented in `secure_app.py`, replaces string concatenation with a **parameterised query**:

```python
query = "SELECT * FROM users WHERE username = ? AND password = ?"
cursor.execute(query, (username, password))
```

The `?` placeholders ensure the SQLite driver treats `username` and `password` strictly as literal data values, never as part of the SQL syntax. The same `' OR '1'='1' -- ` payload, when submitted against `secure_app.py`, is searched for as a literal (non-matching) username and correctly fails to authenticate.

### 2.6 Re-test / Verification

- **Manual:** the payload was resubmitted against `secure_app.py` via the browser and correctly returned "incorrect details."
- **Automated:** `exploits/sql_exploits.py` was re-run against `secure_app.py` and reported the injection as unsuccessful, matching the manual result.

---

## 3. Vulnerability 2: Reflected Cross-Site Scripting (XSS)

### 3.1 Description

The search route in `vulnerable-app.py` takes a user-supplied query parameter and inserts it directly into the HTML response without any escaping:

```python
query = request.args.get('q', '')
return render_template_string('''
    ...
    <h3>Results for: ''' + query + '''</h3>
''')
```

Because `query` is concatenated directly into the HTML string, any HTML or JavaScript it contains is interpreted literally by the browser as part of the page, rather than displayed as plain text.

### 3.2 Exploitation

Submitting the following as a search term:
```
<script>alert('XSS')</script>
```
caused the browser to execute the injected script immediately, displaying a JavaScript alert box. Inspecting the page's HTML confirmed the script tag was present unescaped, directly within the `<h3>` element.

A second payload was tested to demonstrate realistic attacker impact beyond a simple alert:
```
<script>alert(document.cookie)</script>
```
This confirmed that arbitrary JavaScript — including code capable of reading `document.cookie` — executes in the context of the page. This specific demo application does not set any cookies, so the resulting alert was empty; however, the successful execution demonstrates that against a real application using cookies for session management, this technique could be used to exfiltrate session tokens or other sensitive data accessible to client-side JavaScript.

### 3.3 Impact

Reflected XSS allows an attacker to execute arbitrary JavaScript in a victim's browser, typically by tricking the victim into clicking a crafted link containing the malicious payload in the URL. Depending on the application, this could be used to steal session cookies, perform actions on behalf of the victim, redirect to phishing pages, or deface the page content.

### 3.4 Root Cause

User input was inserted into the HTML response as raw, unescaped text, with no distinction made between "content to display" and "markup to render." The browser cannot tell the difference between legitimate page markup and injected attacker content once both are merged into the same unescaped string.

### 3.5 Remediation

The fix, implemented in `secure_app.py`, replaces direct string concatenation with Jinja2's templating syntax:

```python
return render_template_string('''
    ...
    <h3>Results for: {{ query }}</h3>
''', query=query)
```

Jinja2 auto-escapes variables inserted via `{{ }}` by default, converting characters such as `<` and `>` into their safe HTML entity equivalents (`&lt;`, `&gt;`). As a result, an injected payload is rendered as inert, visible text on the page rather than being executed as a real HTML element.

### 3.6 Re-test / Verification

- **Manual:** the same `<script>alert('XSS')</script>` payload was resubmitted against `secure_app.py`. No alert was triggered; the payload instead appeared as literal visible text on the page.

Screenshot evidence: `screenshots/xss_alert_popup.png`, `screenshots/xss_unescaped_source.png`, `screenshots/xss_cookie_attempt.png` (all captured against the vulnerable app).

---

## 4. General Observations & Further Hardening

Beyond the two vulnerabilities addressed in this project, the following would be necessary before any version of this application could be considered for real-world deployment:

- **Password storage:** both versions currently store passwords in plaintext. A production application should hash passwords (e.g. using `werkzeug.security.generate_password_hash`) and never store or compare them in plaintext.
- **Debug mode:** both apps run with `debug=True`, which is appropriate for local development but must never be enabled in production, as it can expose a debugger console and detailed stack traces to end users.
- **Additional defence-in-depth measures** such as a Content Security Policy (CSP) header, input length/format validation, rate limiting on the login endpoint, and CSRF protection on form submissions would further reduce risk even if a similar coding mistake were made in the future.

## 5. Conclusion

This project demonstrates the full lifecycle of two common web vulnerabilities — from root cause, through manual and automated exploitation, to remediation and verified re-testing. Both vulnerabilities shared a common underlying theme: **failing to separate user-supplied data from executable code or markup**. Addressing this distinction — via parameterised queries for SQL and auto-escaping templates for HTML — was sufficient to remediate both issues completely, as confirmed by re-testing with the same exploit payloads and scripts used against the vulnerable version.