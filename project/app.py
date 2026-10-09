from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'conf2027_secret_key_demo'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            login     TEXT NOT NULL UNIQUE,
            password  TEXT NOT NULL,
            fullname  TEXT NOT NULL,
            phone     TEXT NOT NULL,
            email     TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'user'
        )
    """)
    conn.commit()
    conn.close()

def validate_registration(login, password, fullname, phone, email):
    errors = []

    if not re.fullmatch(r'[A-Za-z0-9]{6,}', login):
        errors.append('Логин: только латиница и цифры, минимум 6 символов')

    if len(password) < 8:
        errors.append('Пароль: минимум 8 символов')

    if not re.fullmatch(r'[А-Яа-яЁё\s]+', fullname):
        errors.append('ФИО: только кириллица и пробелы')

    if not re.fullmatch(r'8\(\d{3}\)\d{3}-\d{2}-\d{2}', phone):
        errors.append('Телефон: формат 8(XXX)XXX-XX-XX')

    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        errors.append('Email: некорректный формат')

    return errors

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = []

    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        fullname = request.form.get('fullname', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()

        errors = validate_registration(login, password, fullname, phone, email)

        if not errors:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (login, password, fullname, phone, email) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (login, hash_password(password), fullname, phone, email)
                )
                conn.commit()
                conn.close()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                errors.append('Логин уже занят')
                conn.close()

    return render_template('register.html', errors=errors)

@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password = request.form.get('password', '')

        if not login_val or not password:
            errors.append('Заполните все поля')

        else:
            conn = get_db()
            user = conn.execute(
                "SELECT * FROM users WHERE login = ?", (login_val,)
            ).fetchone()
            conn.close()

            if user and user['password'] == hash_password(password):
                session['user_id'] = user['id']
                session['login'] = user['login']
                session['role'] = user['role']
                return redirect(url_for('login'))

            else:
                errors.append('Неверный логин или пароль')

    return render_template('login.html', errors=errors)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8080, debug=True)