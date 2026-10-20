# Vulnerable Flask App — SQL Injection & XSS Demo

**For portfolio purposes only. Do not deploy or use this application publicly.**

## Overview

This project demonstrates how small logical errors in web application code can expose an entire system's security. It contains two versions of the same Flask web app: `vulnerable-app.py`, which intentionally contains a SQL injection vulnerability in its login form and a  XSS vulnerability in its search feature, and `secure_app.py`, which fixes both using queries with parameters and proper output escaping. An exploit script, `exploits/sql_exploits.py`, automates the SQL injection attack to demonstrate how an attacker could bypass authentication without valid login data.

## Vulnerabilities Demonstrated

- **SQL Injection (login form)** — the vulnerable login route builds its SQL query by directly concatenating user input into the query string. This allows an attacker to alter the query's logic (for example, using a payload like `' OR '1'='1' -- `) to bypass authentication entirely, without knowing a valid username or password.
- **XSS (search feature)** — the vulnerable search route inserts the user's search term directly into the HTML response without escaping it. This allows an attacker to inject an executable script (e.g. `<script>alert('XSS')</script>`) that runs in the victim's browser.

## Project Structure


├── vulnerable-app.py       # Intentionally vulnerable Flask app (SQLi + XSS)
├── secure_app.py           # Fixed version: Queries with parameters + auto-escaping
├── requirements.txt        # Python dependencies
├── exploits/
│   └── sql_exploits.py     # Automated SQL injection exploit script
├── screenshots/            # Evidence of successful exploitation
├── writeup.md              # Detailed vulnerability write up
└── README.md


Note: both apps create their own local SQLite database (`users.db`) automatically on first run, seeded with two test accounts. The database file itself is not committed to this repository (see `.gitignore`).

## Setup

1. Clone this repository:
   -- git clone https://github.com/Ruben-G-CS/vulnerable-flask-app.git
   -- cd vulnerable-flask-app

2. Create and activate a virtual environment:
   -- python3 -m venv venv (mac version)
   -- source venv/bin/activate

3. Install dependencies:
   -- pip install -r requirements.txt

## Running the Vulnerable App

```bash
python vulnerable-app.py
```

Then visit:
- `http://127.0.0.1:5000/login` — vulnerable login form
- `http://127.0.0.1:5000/search` — vulnerable search feature

Test credentials (for normal, non-exploit use): `John` / `Password123`

## Running the Secure App

```bash
python secure_app.py
```

Runs on the same routes and port as above, but with both vulnerabilities fixed. The same exploit payloads that succeed against `vulnerable-app.py` will fail safely against `secure_app.py`.

## Reproducing the Exploits

**SQL Injection (manual):**
On the login form, enter:
- Username: `' OR '1'='1' -- `
- Password: anything you want

Against `vulnerable-app.py`, this logs in without valid credentials. Against `secure_app.py`, it fails.

**SQL Injection (scripted):**
With either app running, in a separate terminal:
```bash
python exploits/sql_exploits.py
```
Reports whether the injection succeeded.

**Reflected XSS (manual):**
On the search page, enter:
```
<script>alert('XSS')</script>
```
Against `vulnerable-app.py`, this triggers an alert popup. Against `secure_app.py`, the payload is displayed as harmless literal text instead of executing.

## The Fixes

- **SQL Injection** — fixed using parameterised queries (`cursor.execute(query, (username, password))`), so user input is always treated as data, never as part of the SQL command itself.
- **XSS** — fixed by using Jinja2's `{{ variable }}` templating syntax, which auto-escapes special HTML characters by default, instead of concatenating raw user input into the HTML string.

Full technical detail, including root cause analysis and before/after evidence, is in [`writeup.md`](./writeup.md).

## Disclaimer

This application was built as a learning exercise to demonstrate, exploit, and remediate common web vulnerabilities. It is intentionally insecure in its `vulnerable-app.py` form and must never be deployed or exposed to a network beyond `127.0.0.1` (localhost).